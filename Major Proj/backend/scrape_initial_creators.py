"""
Initial Creator Scraping Script
Scrapes a small batch of creators to test the system
"""
import sys
sys.path.append('e:/Coding Practice/Python Projects/Python-Projects/Major Proj/backend')

from app.services.intelligence.creator_scraper import creator_scraper
from app.services.intelligence.vector_store import vector_store
import numpy as np
import json

print("=" * 60)
print("INITIAL CREATOR SCRAPING")
print("=" * 60)

# Scrape tech creators (small batch for testing)
print("\n🔍 Scraping Tech Creators...")
print("Keywords: programming tutorials, web development")

tech_creators = creator_scraper.scrape_niche(
    niche='tech',
    keywords=['programming tutorials', 'web development'],
    max_per_keyword=10  # 10 channels per keyword = ~20 total
)

print(f"\n✅ Scraped {len(tech_creators)} tech creators")

# Show sample
if tech_creators:
    print("\n📊 Sample Creators:")
    for i, creator in enumerate(tech_creators[:5], 1):
        print(f"\n{i}. {creator['name']}")
        print(f"   Subscribers: {creator['subscriber_count']:,}")
        print(f"   Tags: {', '.join(creator['tags'])}")
        print(f"   Content samples: {len(creator['content_samples'])} videos")

# Build FAISS index from scraped creators
print("\n" + "=" * 60)
print("BUILDING FAISS INDEX")
print("=" * 60)

if tech_creators:
    # Extract embeddings
    embeddings = np.array([c['embedding'] for c in tech_creators]).astype('float32')
    creator_ids = [c['id'] for c in tech_creators]
    metadata = [{
        'name': c['name'],
        'platform': c['platform'],
        'tags': c['tags'],
        'follower_count': c['subscriber_count'],
        'language': c['language'],
        'bio': c['bio']
    } for c in tech_creators]
    
    # Build index
    vector_store.build_index(embeddings, creator_ids, metadata)
    print(f"✅ FAISS index built with {len(tech_creators)} creators")

# Test similarity search
print("\n" + "=" * 60)
print("TESTING SIMILARITY SEARCH")
print("=" * 60)

from app.services.intelligence.embedding_service import embedding_service

# Test query: "coding tutorials javascript"
test_query = "coding tutorials javascript programming"
query_embedding = embedding_service.encode_text(test_query)

matches = vector_store.search_similar(query_embedding, k=5)

print(f"\nQuery: '{test_query}'")
print(f"Top 5 matches:")
for i, match in enumerate(matches, 1):
    print(f"\n{i}. {match.metadata['name']}")
    print(f"   Similarity: {match.similarity_score:.3f}")
    print(f"   Tags: {', '.join(match.metadata['tags'][:3])}")

# Quota status
print("\n" + "=" * 60)
print("QUOTA STATUS")
print("=" * 60)

quota = creator_scraper.get_quota_status()
print(f"\nUsed: {quota['used']} / {quota['limit']} units")
print(f"Remaining: {quota['remaining']} units")
print(f"Estimated channels remaining today: ~{quota['remaining'] // 102}")

# Save to JSON for inspection
print("\n" + "=" * 60)
print("SAVING DATA")
print("=" * 60)

with open('scraped_creators.json', 'w') as f:
    # Convert embeddings to lists for JSON
    creators_json = []
    for c in tech_creators:
        c_copy = c.copy()
        if isinstance(c_copy['embedding'], np.ndarray):
            c_copy['embedding'] = c_copy['embedding'].tolist()
        creators_json.append(c_copy)
    
    json.dump(creators_json, f, indent=2)

print(f"✅ Saved {len(tech_creators)} creators to scraped_creators.json")

print("\n" + "=" * 60)
print("SCRAPING COMPLETE!")
print("=" * 60)
print(f"\nNext steps:")
print(f"1. Review scraped_creators.json")
print(f"2. Integrate with profile_analyzer.py")
print(f"3. Test recommendations with real data")
