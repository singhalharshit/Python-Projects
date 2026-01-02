"""
Check database row counts for creators
"""
from sqlalchemy import create_engine, text
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_counts():
    print("Checking database row counts...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check creators count
            result = conn.execute(text("SELECT COUNT(*) FROM creators"))
            creator_count = result.scalar()
            print(f"\nCreators in database: {creator_count}")
            
            # Check non-null embeddings
            result = conn.execute(text("SELECT COUNT(*) FROM creators WHERE embedding IS NOT NULL"))
            embedding_count = result.scalar()
            print(f"Creators with embeddings: {embedding_count}")
            
            # Check niches count
            result = conn.execute(text("SELECT COUNT(*) FROM niches"))
            niche_count = result.scalar()
            print(f"Niches in database: {niche_count}")
            
            if creator_count == 0:
                print("\n❌ No creators found! This explains why competitors list is empty.")
            else:
                print("\n✅ Creators exist. Issue might be in vector search or filtering.")
                
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    check_counts()
