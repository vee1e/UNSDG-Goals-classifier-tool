import os
import re
import base64
import requests
from typing import List, Dict, Tuple
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import numpy as np

# --- SDG label set (name + concise description for stronger semantics) ---
SDG_LABELS = [
    ("SDG 1: No Poverty", "End poverty in all its forms everywhere."),
    ("SDG 2: Zero Hunger", "End hunger, achieve food security, improve nutrition, and promote sustainable agriculture."),
    ("SDG 3: Good Health and Well-being", "Ensure healthy lives and promote well-being for all at all ages."),
    ("SDG 4: Quality Education", "Ensure inclusive and equitable quality education and promote lifelong learning opportunities for all."),
    ("SDG 5: Gender Equality", "Achieve gender equality and empower all women and girls."),
    ("SDG 6: Clean Water and Sanitation", "Ensure availability and sustainable management of water and sanitation for all."),
    ("SDG 7: Affordable and Clean Energy", "Ensure access to affordable, reliable, sustainable and modern energy for all."),
    ("SDG 8: Decent Work and Economic Growth", "Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all."),
    ("SDG 9: Industry, Innovation and Infrastructure", "Build resilient infrastructure, promote inclusive and sustainable industrialization and foster innovation."),
    ("SDG 10: Reduced Inequalities", "Reduce inequality within and among countries."),
    ("SDG 11: Sustainable Cities and Communities", "Make cities and human settlements inclusive, safe, resilient and sustainable."),
    ("SDG 12: Responsible Consumption and Production", "Ensure sustainable consumption and production patterns."),
    ("SDG 13: Climate Action", "Take urgent action to combat climate change and its impacts."),
    ("SDG 14: Life Below Water", "Conserve and sustainably use the oceans, seas and marine resources for sustainable development."),
    ("SDG 15: Life on Land", "Protect, restore and promote sustainable use of terrestrial ecosystems; sustainably manage forests; combat desertification; halt biodiversity loss."),
    ("SDG 16: Peace, Justice and Strong Institutions", "Promote peaceful and inclusive societies, provide access to justice for all, and build effective, accountable institutions at all levels."),
    ("SDG 17: Partnerships for the Goals", "Strengthen the means of implementation and revitalize the global partnership for sustainable development.")
]

SDG_NAMES = [n for (n, _) in SDG_LABELS]
SDG_DESCS = [d for (_, d) in SDG_LABELS]

# --- GitHub fetch utilities ---
GITHUB_API = "https://api.github.com"

def parse_repo(url: str) -> Tuple[str, str]:
    """
    Accepts URLs like https://github.com/owner/repo or owner/repo.
    Returns (owner, repo).
    """
    u = url.strip()
    if u.startswith("http"):
        parts = u.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
    else:
        owner, repo = u.split("/", 1)
    return owner, repo

def gh_get(path: str, params: dict = None, accept_preview: bool = False) -> dict:
    headers = {"User-Agent": "sdg-classifier"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if accept_preview:
        # topics API requires a custom media type on some API versions
        headers["Accept"] = "application/vnd.github.mercy-preview+json, application/vnd.github+json"
    else:
        headers["Accept"] = "application/vnd.github+json"
    r = requests.get(GITHUB_API + path, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def fetch_repo_text(url: str, max_issues: int = 10) -> Dict:
    owner, repo = parse_repo(url)

    repo_data = gh_get(f"/repos/{owner}/{repo}", accept_preview=True)
    name = repo_data.get("name") or ""
    description = repo_data.get("description") or ""
    topics = " ".join(repo_data.get("topics") or [])
    homepage = repo_data.get("homepage") or ""

    # README
    readme = ""
    try:
        rd = gh_get(f"/repos/{owner}/{repo}/readme")
        content_b64 = rd.get("content", "")
        if content_b64:
            readme = base64.b64decode(content_b64).decode(errors="ignore")
    except Exception:
        pass

    # Issues (titles only, open ones)
    issues_texts = []
    try:
        issues = gh_get(f"/repos/{owner}/{repo}/issues", params={"state": "open", "per_page": max_issues})
        for it in issues:
            if "pull_request" not in it:  # skip PRs
                issues_texts.append(it.get("title", ""))
    except Exception:
        pass

    # Concatenate
    corpus = "\n".join([
        name, description, topics, homepage, readme, "\n".join(issues_texts)
    ])

    # Light clean
    corpus = re.sub(r"[ \t]+", " ", corpus)
    corpus = re.sub(r"\n{2,}", "\n", corpus).strip()

    return {
        "owner": owner, "repo": repo, "text": corpus,
        "meta": {"name": name, "description": description, "topics": topics.split(), "homepage": homepage}
    }

# --- Zero-shot and embedding models (lazy-load) ---
_zeroshot = None
_embedder = None

def get_zeroshot():
    global _zeroshot
    if _zeroshot is None:
        _zeroshot = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device_map="auto")
    return _zeroshot

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _embedder

def zero_shot_scores(text: str, labels: List[str]) -> np.ndarray:
    """
    Returns probabilities for each label using NLI zero-shot (multi-label).
    """
    clf = get_zeroshot()
    out = clf(text, labels, multi_label=True)
    # transformers returns in label order provided
    return np.array(out["scores"], dtype=float)

def embedding_similarity_scores(text: str, label_texts: List[str]) -> np.ndarray:
    """
    Cosine similarity between text embedding and each label description.
    """
    emb = get_embedder()
    v_text = emb.encode([text], normalize_embeddings=True)[0]
    v_lbls = emb.encode(label_texts, normalize_embeddings=True)
    sims = np.dot(v_lbls, v_text)  # cosine since normalized
    # Normalize to 0..1
    sims = (sims - sims.min()) / (sims.max() - sims.min() + 1e-8)
    return sims

def ensemble_scores(zs: np.ndarray, es: np.ndarray, alpha: float = 0.5) -> np.ndarray:
    """
    Simple mean ensemble; tune alpha if desired.
    """
    return alpha * zs + (1 - alpha) * es

def classify_repo(url: str, threshold: float = 0.4, top_k: int = 5, use_ensemble: bool = True):
    data = fetch_repo_text(url)
    text = data["text"][:6000]  # cap for speed; increase if needed
    if not text:
        raise ValueError("No text extracted from this repository. Add README or description.")

    # Zero-shot on label NAMES *and* include SDG descriptions for embedding sim
    zs = zero_shot_scores(text, SDG_NAMES)

    if use_ensemble:
        # Embedding similarity against richer label descriptions
        es = embedding_similarity_scores(text, SDG_DESCS)
        scores = ensemble_scores(zs, es, alpha=0.6)  # bias slightly toward zero-shot
    else:
        scores = zs

    # Rank + threshold
    idx = np.argsort(scores)[::-1]
    ranked = [(SDG_NAMES[i], float(scores[i])) for i in idx]

    selected = [(name, sc) for (name, sc) in ranked if sc >= threshold]
    if not selected:
        selected = ranked[:max(1, min(top_k, 3))]

    return {
        "repo": f"{data['owner']}/{data['repo']}",
        "predictions": selected[:top_k],
        "top_all": ranked[:top_k],
        "meta": data["meta"]
    }

if __name__ == "__main__":
    # EXAMPLE:
    test_url = "https://github.com/protontypes/open-sustainable-technology"  
    result = classify_repo(test_url, threshold=0.4, top_k=5, use_ensemble=True)
    print("Repository:", result["repo"])
    print("Predicted SDGs (name, score):")
    for name, sc in result["predictions"]:
        print(f"  - {name}: {sc:.3f}")