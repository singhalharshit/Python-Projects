"""
Test NLP Service
Verifies that Semantic Matching and Clustering works
"""
import sys
from pathlib import Path
import logging

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO)

from app.services.intelligence.nlp_service import nlp_service

def test_nlp():
    print("\n" + "🧠 " + "="*76 + " 🧠")
    print("   TEST: NLP Brain")
    print("🧠 " + "="*76 + " 🧠")
    
    # 1. Similarity
    print("\n1️⃣  Testing Semantic Similarity:")
    pair1 = ("Python", "Coding in Snake Case")
    score1 = nlp_service.compute_similarity(*pair1)
    print(f"   '{pair1[0]}' vs '{pair1[1]}': {score1:.3f}")
    
    pair2 = ("ReactJS", "Front-end Web Development")
    score2 = nlp_service.compute_similarity(*pair2)
    print(f"   '{pair2[0]}' vs '{pair2[1]}': {score2:.3f}")
    
    pair3 = ("Machine Learning", "Cooking Pasta")
    score3 = nlp_service.compute_similarity(*pair3)
    print(f"   '{pair3[0]}' vs '{pair3[1]}': {score3:.3f}")
    
    # 2. Clustering
    print("\n2️⃣  Testing Meta-Trend Clustering:")
    topics = [
        "ReactJS Hooks", "Vue.js Composition API", "Angular Signals", # Frontend
        "Python GIL", "Rust Memory Safety", "C++ Pointers",           # Systems
        "Startup Funding", "VC Term Sheets", "Bootstrapping",         # Business
        "Deep Learning Transformers", "LLM Fine-tuning"               # AI
    ]
    
    clusters = nlp_service.cluster_topics(topics, num_clusters=4)
    
    for cid, items in clusters.items():
        print(f"   Cluster {cid}: {items}")

if __name__ == "__main__":
    test_nlp()
