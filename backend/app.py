import os
# import uuid
# import json
import time
import requests
from flask import Flask, jsonify, request, abort, make_response
from flask_cors import CORS
from datetime import datetime, UTC
from embedding_description import main as classify_description
from embedding_url import main as classify_url
from aurora_api import main as aurora_classify
from cache import classification_cache


app = Flask(__name__)
CORS(app)



# ==================== CACHE HELPERS ====================

def get_cached_or_compute(endpoint: str, data: dict, compute_func, ttl: int = None):
    """
    Helper to check cache before computing result.
    
    Args:
        endpoint: The API endpoint identifier
        data: Request data dictionary
        compute_func: Function to call if cache miss
        ttl: Optional custom TTL
        
    Returns:
        Flask response object with cache headers
    """
    # Try to get from cache
    cached_result, is_hit = classification_cache.get(endpoint, data)
    
    if is_hit:
        # Return cached result with headers
        response = make_response(jsonify(cached_result))
        response.headers['X-Cache'] = 'HIT'
        response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
        return response
    
    # Cache miss - call the compute function
    result, status_code = compute_func()
    
    # Only cache successful responses without errors
    if status_code == 200 and isinstance(result, dict) and 'error' not in result:
        classification_cache.set(endpoint, data, result, ttl)
        response = make_response(jsonify(result))
        response.headers['X-Cache'] = 'MISS'
        return response, status_code
    else:
        response = make_response(jsonify(result))
        return response, status_code


# ==================== API ENDPOINTS ====================

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello, World!'})



def _compute_aurora(data: dict):
    """Compute Aurora classification result."""
    projectName = data.get('projectName')
    projectUrl = data.get('projectUrl')
    projectDescription = data.get('projectDescription')
    
    if not projectDescription:
        return {'error': 'Project description is required'}, 400
    
    # 1. Aurora API Model (text-based)
    print("\n===== RUNNING AURORA API MODEL =====")
    try:
        aurora_result = aurora_classify(
            text=projectDescription,
            project_name=projectName,
            project_url=projectUrl
        )
        print("Aurora API model completed successfully")
    except Exception as e:
        print(f"Aurora API model failed: {str(e)}")
        return {
            "error": str(e),
            "message": "Aurora API classification failed"
        }, 500
    
    # Transform predictions to array format
    sdg_preds = aurora_result.get("sdg_predictions", {})
    if isinstance(sdg_preds, dict):
        preds = [
            {"sdg": name, "prediction": score}
            for name, score in sdg_preds.items()
        ]
    else:
        preds = sdg_preds
    
    filtered_predictions = [p for p in preds if p.get("prediction", 0) > 0.4]
    
    result = {
        "projectName": aurora_result.get("project_name"),
        "projectUrl": aurora_result.get("project_url"),
        "predictions": filtered_predictions
    }
    return result, 200


@app.route('/api/classify_aurora', methods=['POST'])
def classify_aurora():
    data = request.json
    result, status_code = _compute_aurora(data)
    
    # Only cache successful responses
    if status_code == 200 and 'error' not in result:
        cached_result, is_hit = classification_cache.get('aurora', data)
        if is_hit:
            response = make_response(jsonify(cached_result))
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
            return response
        
        classification_cache.set('aurora', data, result)
        response = make_response(jsonify(result))
        response.headers['X-Cache'] = 'MISS'
        return response
    
    return jsonify(result), status_code


def _compute_st_description(data: dict):
    """Compute ST Description classification result."""
    projectName = data.get('projectName')
    projectUrl = data.get('projectUrl')
    projectDescription = data.get('projectDescription')
    
    if not projectDescription:
        return {'error': 'Project description is required'}, 400
    
    # 3. Sentence Transformer Description Model (text-based)
    print("\n===== RUNNING SENTENCE TRANSFORMER DESCRIPTION MODEL =====")
    try:
        st_desc_result = classify_description(
            project_description=projectDescription,
            project_name=projectName,
            project_url=projectUrl
        )
        print("ST Description model completed successfully")
    except Exception as e:
        print(f"ST Description model failed: {str(e)}")
        return {
            "error": str(e),
            "message": "Sentence Transformer Description model classification failed"
        }, 500
    
    # Convert predictions to the expected format
    preds = [
        {"sdg": name, "prediction": score}
        for name, score in st_desc_result.get("sdg_predictions", {}).items()
    ]
    filtered_predictions = [p for p in preds if p.get("prediction", 0) > 0.4]
    
    result = {
        "projectName": projectName,
        "projectUrl": projectUrl,
        "predictions": filtered_predictions,
    }
    return result, 200


@app.route('/api/classify_st_description', methods=['POST'])
def classify_st_description():
    data = request.json
    result, status_code = _compute_st_description(data)
    
    # Only cache successful responses
    if status_code == 200 and 'error' not in result:
        cached_result, is_hit = classification_cache.get('st-description', data)
        if is_hit:
            response = make_response(jsonify(cached_result))
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
            return response
        
        classification_cache.set('st-description', data, result)
        response = make_response(jsonify(result))
        response.headers['X-Cache'] = 'MISS'
        return response
    
    return jsonify(result), status_code


def _compute_st_url(data: dict):
    """Compute ST URL classification result."""
    projectName = data.get('projectName')
    projectUrl = data.get('projectUrl')
    projectDescription = data.get('projectDescription')
    
    if not projectDescription:
        return {'error': 'Project description is required'}, 400
    
    # 2. Sentence Transformer URL Model (GitHub URL-based)
    print("\n===== RUNNING SENTENCE TRANSFORMER URL MODEL =====")
    if projectUrl:
        try:
            st_url_result = classify_url(projectUrl)
            print("ST URL model completed successfully")
        except ValueError as ve:
            print(f"ST URL model invalid URL: {str(ve)}")
            return {'error': str(ve)}, 400
        except requests.exceptions.HTTPError as he:
            print(f"ST URL model HTTP Error: {str(he)}")
            return {
                "error": f"Failed to fetch repository data. Please ensure the repository is public and exists. ({str(he)})",
                "message": "Sentence Transformer URL model classification failed"
            }, 400
        except Exception as e:
            print(f"ST URL model failed: {str(e)}")
            return {
                "error": str(e),
                "message": "Sentence Transformer URL model classification failed"
            }, 500
    else:
        return {
            "error": "No project URL provided",
            "message": "URL-based classification requires a GitHub URL"
        }, 400
    
    preds = [
        {"sdg": name, "prediction": score}
        for name, score in st_url_result.get("sdg_predictions", {}).items()
    ]
    filtered_predictions = [p for p in preds if p.get("prediction", 0) > 0.4]
    
    result = {
        "projectName": projectName,
        "projectUrl": projectUrl,
        "predictions": filtered_predictions,
    }
    return result, 200


@app.route('/api/classify_st_url', methods=['POST'])
def classify_st_url():
    data = request.json
    result, status_code = _compute_st_url(data)
    
    # Only cache successful responses
    if status_code == 200 and 'error' not in result:
        cached_result, is_hit = classification_cache.get('st-url', data)
        if is_hit:
            response = make_response(jsonify(cached_result))
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
            return response
        
        classification_cache.set('st-url', data, result)
        response = make_response(jsonify(result))
        response.headers['X-Cache'] = 'MISS'
        return response
    
    return jsonify(result), status_code

def _compute_osdg(data: dict):
    """Compute OSDG API classification result."""
    projectName = data.get('projectName')
    projectUrl = data.get('projectUrl')
    projectDescription = data.get('projectDescription')
    
    if not projectDescription:
        return {'error': 'Project description is required'}, 400
    
    # Call the external OSDG API
    try:
        osdg_response = requests.post(
            "http://20.73.166.85/label_text",
            json={"text": projectDescription},
            headers={"token": os.environ.get("OSDG_TOKEN")},
            timeout=1000
        )
        osdg_response.raise_for_status()
        osdg_result = osdg_response.json()
    except requests.exceptions.RequestException as e:
        print(f"OSDG API request failed: {str(e)}")
        return {
            "error": f"Failed to connect to OSDG API: {str(e)}",
            "message": "OSDG API classification failed"
        }, 500
    
    result = {
        "projectName": projectName,
        "projectUrl": projectUrl,
        "predictions": osdg_result
    }
    return result, 200


@app.route("/api/osdg_api", methods=["POST"])
def osdg_external_api():
    data = request.json
    result, status_code = _compute_osdg(data)
    
    # Only cache successful responses
    if status_code == 200 and 'error' not in result:
        cached_result, is_hit = classification_cache.get('osdg', data)
        if is_hit:
            response = make_response(jsonify(cached_result))
            response.headers['X-Cache'] = 'HIT'
            response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
            return response
        
        classification_cache.set('osdg', data, result)
        response = make_response(jsonify(result))
        response.headers['X-Cache'] = 'MISS'
        return response
    
    return jsonify(result), status_code


# ==================== CACHE MANAGEMENT ENDPOINTS ====================

@app.route('/api/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics including hit rate, size, and performance metrics."""
    stats = classification_cache.get_stats()
    return jsonify({
        "cache_stats": stats,
        "status": "healthy" if stats['active_entries'] < 1000 else "warning"
    }), 200


@app.route('/api/cache/clear', methods=['POST'])
def cache_clear():
    """Clear all cached entries. Useful for testing or when models are updated."""
    classification_cache.clear()
    return jsonify({
        "message": "Cache cleared successfully",
        "timestamp": time.time()
    }), 200


@app.route('/api/cache/inspect', methods=['POST'])
def cache_inspect():
    """
    Inspect what cache key would be generated for a request.
    Useful for debugging cache behavior.
    """
    data = request.json or {}
    endpoint = data.get('endpoint', 'unknown')
    
    cache_key = classification_cache.get_cache_key(endpoint, data)
    
    return jsonify({
        "endpoint": endpoint,
        "cache_key": cache_key,
        "request_data": {
            "projectUrl": data.get('projectUrl'),
            "projectDescription_preview": data.get('projectDescription', '')[:100] + "..." if data.get('projectDescription') else None
        }
    }), 200


# @app.post("/api/upload-md")
# def aurora_api():

#     project_name = request.form.get("project_name", "").strip()
#     project_url = request.form.get("project_url", "").strip()

#     if not project_name:
#         return jsonify({"error": "Project name is required"}), 400
#     if not project_url:
#         return jsonify({"error": "Project URL is required"}), 400


#     if "file" not in request.files:
#         return jsonify({"error":"No file part named 'file' in form-data."}), 400
#     f = request.files["file"]

#     if f.filename == "":
#         return jsonify({ "error": "Empty filename."}), 400
#     if not allowed_ext(f.filename):
#         return jsonify({"error" : "Only .md files are allowed."}), 400


#     filename = secure_filename(f.filename)

#     text = f.read().decode("utf-8", errors="replace")

#     result = aurora_main(text)

#     return jsonify({
#         "project_name": project_name,
#         "project_url": project_url,
#         "filename": filename,
#         "size_bytes": len(text.encode("utf-8")),
#         "content_preview": text[:2000],
#         "predictions": result.get("predictions", "")
#     }), 200

if __name__ == '__main__':
    app.run(debug=True)
