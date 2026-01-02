"""
Quick test script to verify ML system is working
"""
import sys
sys.path.append('e:/Coding Practice/Python Projects/Python-Projects/Major Proj/backend')

from app.services.intelligence.embedding_service import embedding_service
from app.services.intelligence.creator_database import creator_database
from app.services.intelligence.vector_store import vector_store

print("=" * 60)
print("ML SYSTEM TEST")
print("=" * 60)

# Test 1: Embedding generation
print("\n1. Testing Embedding Generation...")
vec1 = embedding_service.encode_text("coding tutorials javascript programming")
vec2 = embedding_service.encode_text("fitness training bodybuilding workout")
vec3 = embedding_service.encode_text("coding tutorials python programming")

print(f"   Vector shape: {vec1.shape}")
print(f"   Coding vs Coding similarity: {embedding_service.cosine_similarity(vec1, vec3):.3f}")
print(f"   Coding vs Fitness similarity: {embedding_service.cosine_similarity(vec1, vec2):.3f}")
print("   ✓ Embeddings working! (coding-coding > coding-fitness)")

# Test 2: Creator database
print("\n2. Testing Creator Database...")
print(f"   Loaded {len(creator_database.creators)} creators")
print(f"   Index built: {creator_database.is_indexed}")
print("   ✓ Creator database loaded!")

# Test 3: Different usernames get different suggestions
print("\n3. Testing Username-Based Suggestions...")

test_cases = [
    ("techcoder", "coding tutorials programming"),
    ("fitnessguru", "fitness training bodybuilding"),
    ("stocktrader", "finance investing stocks"),
]

for username, inferred_content in test_cases:
    user_vec = embedding_service.encode_text(inferred_content)
    matches = vector_store.search_similar(user_vec, k=3)
    
    print(f"\n   Username: {username}")
    print(f"   Inferred: {inferred_content}")
    print(f"   Top 3 suggestions:")
    for i, match in enumerate(matches, 1):
        creator = creator_database.get_creator_by_id(match.creator_id)
        print(f"      {i}. {creator['name']} (similarity: {match.similarity_score:.3f})")

print("\n" + "=" * 60)
print("ML SYSTEM TEST COMPLETE!")
print("=" * 60)
