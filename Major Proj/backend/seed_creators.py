"""
Seed Database with Real Instagram Creators
This populates the vector store and database with real creator data
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import numpy as np
    from datetime import datetime
    from app.services.intelligence.vector_store import get_vector_store
    from app.services.intelligence.embedding_service import EmbeddingService
    from app.core.database import SessionLocal
    
    print("🌱 Seeding database with real Instagram creators...")
    print("="*60)
    
    # Initialize services
    vector_store = get_vector_store()
    embedding_service = EmbeddingService()
    db = SessionLocal()
    
    # Real Instagram creators by niche
    SEED_CREATORS = [
        # Tech/AI Niche
        {"username": "mkbhd", "name": "MKBHD", "bio": "Tech reviews and tutorials", "followers": 19000000, "niche": "tech"},
        {"username": "unboxtherapy", "name": "Unbox Therapy", "bio": "Unboxing latest tech gadgets", "followers": 18000000, "niche": "tech"},
        {"username": "mkbsd", "name": "Marques Brownlee", "bio": "Quality tech videos", "followers": 17000000, "niche": "tech"},
        {"username": "austinnotduncan", "name": "Austin Evans", "bio": "Tech reviews and comparisons", "followers": 5000000, "niche": "tech"},
        {"username": "ijustine", "name": "iJustine", "bio": "Tech lifestyle and unboxing", "followers": 7000000, "niche": "tech"},
        
        # AI/ML Niche
        {"username": "lexfridman", "name": "Lex Fridman", "bio": "AI researcher and podcast host", "followers": 3000000, "niche": "ai"},
        {"username": "andrewng", "name": "Andrew Ng", "bio": "AI education and deep learning", "followers": 2000000, "niche": "ai"},
        {"username": "deeplearningai", "name": "DeepLearning.AI", "bio": "AI courses and tutorials", "followers": 1000000, "niche": "ai"},
        
        # Fitness Niche
        {"username": "therock", "name": "Dwayne Johnson", "bio": "Fitness motivation and training", "followers": 395000000, "niche": "fitness"},
        {"username": "chrishemsworth", "name": "Chris Hemsworth", "bio": "Fitness and workout routines", "followers": 57000000, "niche": "fitness"},
        {"username": "jlo", "name": "Jennifer Lopez", "bio": "Dance fitness and wellness", "followers": 250000000, "niche": "fitness"},
        {"username": "kayla_itsines", "name": "Kayla Itsines", "bio": "Fitness programs and workouts", "followers": 16000000, "niche": "fitness"},
        {"username": "sweat", "name": "Sweat", "bio": "Fitness app and community", "followers": 2000000, "niche": "fitness"},
        
        # Cooking/Food Niche
        {"username": "gordonramsayofficial", "name": "Gordon Ramsay", "bio": "Chef and cooking tutorials", "followers": 15000000, "niche": "cooking"},
        {"username": "jamieoliver", "name": "Jamie Oliver", "bio": "Easy recipes and cooking", "followers": 10000000, "niche": "cooking"},
        {"username": "tasty", "name": "Tasty", "bio": "Quick recipe videos", "followers": 45000000, "niche": "cooking"},
        {"username": "foodnetwork", "name": "Food Network", "bio": "Recipes and cooking shows", "followers": 14000000, "niche": "cooking"},
        
        # Fashion/Beauty Niche
        {"username": "hudabeauty", "name": "Huda Kattan", "bio": "Beauty tips and makeup", "followers": 53000000, "niche": "beauty"},
        {"username": "jamescharles", "name": "James Charles", "bio": "Makeup artist and beauty", "followers": 24000000, "niche": "beauty"},
        {"username": "nikkietutorials", "name": "NikkieTutorials", "bio": "Makeup tutorials", "followers": 19000000, "niche": "beauty"},
        {"username": "zendaya", "name": "Zendaya", "bio": "Fashion and beauty icon", "followers": 184000000, "niche": "fashion"},
        
        # Travel Niche
        {"username": "beautifuldestinations", "name": "Beautiful Destinations", "bio": "Travel photography", "followers": 16000000, "niche": "travel"},
        {"username": "muradosmann", "name": "Murad Osmann", "bio": "Travel photography series", "followers": 6000000, "niche": "travel"},
        {"username": "earthpix", "name": "EarthPix", "bio": "Nature and travel photos", "followers": 24000000, "niche": "travel"},
        
        # Business/Entrepreneur Niche
        {"username": "garyvee", "name": "Gary Vaynerchuk", "bio": "Business and entrepreneurship", "followers": 11000000, "niche": "business"},
        {"username": "elonmusk", "name": "Elon Musk", "bio": "Tech entrepreneur and CEO", "followers": 200000000, "niche": "business"},
        {"username": "thesharkdaymond", "name": "Daymond John", "bio": "Entrepreneur and investor", "followers": 2000000, "niche": "business"},
        
        # Photography Niche
        {"username": "natgeo", "name": "National Geographic", "bio": "Wildlife and nature photography", "followers": 283000000, "niche": "photography"},
        {"username": "peterlik", "name": "Peter Lik", "bio": "Landscape photographer", "followers": 2000000, "niche": "photography"},
        
        # Music Niche
        {"username": "taylorswift", "name": "Taylor Swift", "bio": "Music and lifestyle", "followers": 283000000, "niche": "music"},
        {"username": "arianagrande", "name": "Ariana Grande", "bio": "Pop music artist", "followers": 380000000, "niche": "music"},
        {"username": "justinbieber", "name": "Justin Bieber", "bio": "Music and entertainment", "followers": 295000000, "niche": "music"},
        
        # Gaming Niche
        {"username": "ninja", "name": "Ninja", "bio": "Professional gamer and streamer", "followers": 24000000, "niche": "gaming"},
        {"username": "pokimane", "name": "Pokimane", "bio": "Gaming content creator", "followers": 9000000, "niche": "gaming"},
        
        # Comedy Niche
        {"username": "kevinhart4real", "name": "Kevin Hart", "bio": "Comedian and actor", "followers": 179000000, "niche": "comedy"},
        {"username": "theellenshow", "name": "Ellen DeGeneres", "bio": "Comedy and talk show", "followers": 139000000, "niche": "comedy"},
    ]
    
    print(f"Adding {len(SEED_CREATORS)} creators to database...\n")
    
    added_count = 0
    for creator in SEED_CREATORS:
        try:
            # Generate embedding from bio
            bio_text = f"{creator['name']} {creator['bio']} {creator['niche']}"
            embedding = embedding_service.encode_text(bio_text)
            
            # Add to vector store
            vector_store.add_creator(
                creator_id=creator['username'],
                embedding=embedding,
                metadata={
                    'name': creator['name'],
                    'bio': creator['bio'],
                    'followers': creator['followers'],
                    'niche': creator['niche'],
                    'platform': 'instagram',
                    'seeded_at': datetime.utcnow().isoformat()
                }
            )
            
            added_count += 1
            print(f"✅ Added @{creator['username']} ({creator['niche']}) - {creator['followers']:,} followers")
            
        except Exception as e:
            print(f"❌ Failed to add @{creator['username']}: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully added {added_count}/{len(SEED_CREATORS)} creators")
    print(f"{'='*60}\n")
    
    # Test vector store
    print("Testing vector store...")
    sample_query = embedding_service.encode_text("tech reviews and gadgets")
    results = vector_store.search(sample_query, k=5)
    
    if results:
        print(f"\n✅ Vector store working! Found {len(results)} similar creators:")
        for i, result in enumerate(results[:5], 1):
            print(f"  {i}. @{result['user_id']} (score: {result.get('score', 0):.3f})")
    else:
        print("\n⚠️  Vector store search returned no results")
    
    print("\n🎉 Seeding complete! Restart backend to use the data.")
