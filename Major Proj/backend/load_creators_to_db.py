"""
Load Scraped Creators into Database
Reads scraped_creators.json and inserts into PostgreSQL
"""
import sys
sys.path.append('e:/Coding Practice/Python Projects/Python-Projects/Major Proj/backend')

import json
import logging
from app.core.database import SessionLocal
from sqlalchemy import text
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_creators():
    try:
        # Load JSON data
        with open('scraped_creators.json', 'r') as f:
            creators = json.load(f)
        
        logger.info(f"Loaded {len(creators)} creators from JSON")
        
        db = SessionLocal()
        
        # Clear existing data (optional, for clean slate)
        # db.execute(text("TRUNCATE TABLE creators"))
        # db.commit()
        
        inserted_count = 0
        updated_count = 0
        
        for c in creators:
            # Check if exists
            exists = db.execute(
                text("SELECT 1 FROM creators WHERE id = :id"),
                {"id": c['id']}
            ).fetchone()
            
            embedding_list = c['embedding']
            if isinstance(embedding_list, np.ndarray):
                embedding_list = embedding_list.tolist()
            
            params = {
                "id": c['id'],
                "platform": c['platform'],
                "name": c['name'],
                "handle": c.get('handle'),
                "bio": c.get('bio'),
                "subscriber_count": c['subscriber_count'],
                "language": c.get('language', 'en'),
                "niche": c.get('niche'),
                "embedding": embedding_list,
                "content_samples": json.dumps(c.get('content_samples', [])),
                "tags": json.dumps(c.get('tags', [])),
                "metadata": json.dumps(c.get('metadata', {}))
            }
            
            if exists:
                # Update
                sql = text("""
                    UPDATE creators SET
                        platform = :platform,
                        name = :name,
                        handle = :handle,
                        bio = :bio,
                        subscriber_count = :subscriber_count,
                        language = :language,
                        niche = :niche,
                        embedding = :embedding,
                        content_samples = :content_samples,
                        tags = :tags,
                        metadata = :metadata,
                        updated_at = NOW()
                    WHERE id = :id
                """)
                updated_count += 1
            else:
                # Insert
                sql = text("""
                    INSERT INTO creators (
                        id, platform, name, handle, bio, subscriber_count,
                        language, niche, embedding, content_samples, tags, metadata
                    ) VALUES (
                        :id, :platform, :name, :handle, :bio, :subscriber_count,
                        :language, :niche, :embedding, :content_samples, :tags, :metadata
                    )
                """)
                inserted_count += 1
                
            db.execute(sql, params)
        
        db.commit()
        logger.info(f"Success! Inserted: {inserted_count}, Updated: {updated_count}")
        
    except Exception as e:
        logger.error(f"Error loading creators: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_creators()
