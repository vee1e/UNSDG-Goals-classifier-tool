"""
SDG (Sustainable Development Goals) Constants
Centralized storage for SDG labels and descriptions used across classification models.
"""

# SDG number to name mapping (used by Aurora API)
SDG_LABELS_DICT = {
    "1": "No Poverty",
    "2": "Zero Hunger",
    "3": "Good Health and Well-being",
    "4": "Quality Education",
    "5": "Gender Equality",
    "6": "Clean Water and Sanitation",
    "7": "Affordable and Clean Energy",
    "8": "Decent Work and Economic Growth",
    "9": "Industry, Innovation and Infrastructure",
    "10": "Reduced Inequalities",
    "11": "Sustainable Cities and Communities",
    "12": "Responsible Consumption and Production",
    "13": "Climate Action",
    "14": "Life Below Water",
    "15": "Life on Land",
    "16": "Peace, Justice and Strong Institutions",
    "17": "Partnerships for the Goals"
}

# SDG labels with full names and descriptions (used by embedding models)
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

# Derived constants for convenience
SDG_NAMES = [n for (n, _) in SDG_LABELS]
SDG_DESCS = [d for (_, d) in SDG_LABELS]
