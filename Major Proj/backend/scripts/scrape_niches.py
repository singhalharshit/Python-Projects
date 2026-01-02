
import os
import sys
import time
from typing import List

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.intelligence.youtube_scraper import youtube_scraper
from app.services.intelligence.embedding_service import embedding_service
from app.services.intelligence.creator_database import creator_database
from app.services.intelligence.vector_store import vector_store

def extract_tags(corpus: str) -> List[str]:
    # Simple tag extraction
    words = corpus.lower().split()
    # Filter common words and keep interesting ones (very basic)
    STOPWORDS = {'the', 'and', 'is', 'in', 'to', 'for', 'of', 'with', 'a', 'on'}
    tags = [w for w in words if len(w) > 4 and w not in STOPWORDS]
    from collections import Counter
    return [t for t, c in Counter(tags).most_common(5)]

def infer_niche(query: str) -> str:
    if "programming" in query or "coding" in query: return "coding"
    if "fitness" in query or "workout" in query: return "fitness"
    if "finance" in query: return "finance"
    if "gaming" in query: return "gaming"
    if "lifestyle" in query: return "lifestyle"
    return "general"

def scrape_niche(niche_name: str, queries: List[str]):
    print(f"\n--- Scraping Niche: {niche_name} ---")
    
    for query in queries:
        print(f"Searching for: {query}")
        channels = youtube_scraper.search_channels(query, max_results=15)
        
        for channel in channels:
            if creator_database.get_creator_by_id(channel['id']):
                print(f"Skipping {channel['title']} (exists)")
                continue
                
            print(f"Processing {channel['title']}...")
            
            # Get details
            details = youtube_scraper.get_channel_details(channel['id'])
            if not details: continue
            
            # Get videos
            videos = youtube_scraper.get_recent_videos(channel['id'], max_results=10)
            
            # Corpus
            corpus = youtube_scraper.extract_content_corpus(details, videos)
            
            # Embedding
            embedding = embedding_service.encode_text(corpus)
            
            # Save
            creator_database.add_creator(
                id=channel['id'],
                platform="youtube",
                name=details['name'],
                handle=details.get('custom_url'),
                bio=details['description'],
                follower_count=details['subscriber_count'],
                embedding=embedding,
                metadata={
                    'views': details['view_count'],
                    'videos': details['video_count'],
                    'country': details['country']
                },
                content_samples=[v['title'] for v in videos],
                tags=extract_tags(corpus),
                niche=niche_name,
                content_style="Educational" if niche_name == "coding" else "Entertainment"
            )
            print(f"Saved {details['name']}")
            time.sleep(0.5) # Be nice to API

def main():
    # Setup
    creator_database.load_creators()
    
    # Niches to scrape
    NICHES = {
        "fitness": ["fitness training", "workout tips", "bodybuilding", "yoga at home"],
        "finance": ["personal finance", "investing for beginners", "stock market analysis"],
        "gaming": ["gaming news", "minecraft gameplay", "valorant highlights"],
        "lifestyle": ["daily vlog", "minimalism lifestyle", "productivity tips"]
    }
    
    try:
        for niche, queries in NICHES.items():
            scrape_niche(niche, queries)
            
        # Rebuild index
        print("\nRebuilding Vector Index...")
        creator_database.build_index()
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
