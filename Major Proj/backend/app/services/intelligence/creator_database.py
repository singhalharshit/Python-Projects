"""
Creator Database
Manages creator embeddings and metadata for ML-based recommendations
"""
import logging
from typing import List, Dict, Any
import numpy as np
import json
from app.services.intelligence.embedding_service import embedding_service
from app.services.intelligence.vector_store import vector_store
from app.core.database import SessionLocal
from sqlalchemy import text

logger = logging.getLogger(__name__)


class CreatorDatabase:
    """
    Manages creator data and embeddings.
    Fetches from PostgreSQL database.
    """
    
    def __init__(self):
        self.creators = []
        self.is_indexed = False
    
    def load_creators(self):
        """
        Load creator data from database.
        """
        logger.info("Loading creator database from PostgreSQL...")
        
        try:
            # Try fetching from DB
            logger.info("Connecting to database...")
            db = SessionLocal()
            result = db.execute(text("SELECT * FROM creators"))
            rows = result.fetchall()
            db.close()
            
            self.creators = []
            for row in rows:
                content_samples = row.content_samples
                if isinstance(content_samples, str):
                    content_samples = json.loads(content_samples)
                
                tags = row.tags
                if isinstance(tags, str):
                    tags = json.loads(tags)
                
                metadata = row.metadata
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                
                embedding = row.embedding
                if isinstance(embedding, str):
                    embedding = json.loads(embedding)
                
                creator = {
                    "id": row.id,
                    "name": row.name,
                    "platform": row.platform,
                    "bio": row.bio,
                    "content_samples": content_samples,
                    "tags": tags,
                    "follower_count": row.subscriber_count,
                    "language": row.language,
                    "niche": row.niche,
                    "embedding": embedding,
                    "avg_views": metadata.get("view_count", "N/A"),
                    "handle": row.handle
                }
                self.creators.append(creator)
            
            logger.info(f"Loaded {len(self.creators)} creators from DB")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            logger.info("Falling back to scraped_creators.json...")
            
            try:
                import os
                # Look for file in backend directory
                json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'scraped_creators.json')
                
                if not os.path.exists(json_path):
                    # Try current directory
                    json_path = 'scraped_creators.json'
                
                if os.path.exists(json_path):
                    with open(json_path, 'r') as f:
                        json_creators = json.load(f)
                    
                    # Normalize JSON data to match DB structure
                    self.creators = []
                    for c in json_creators:
                        # Ensure we have follower_count (mapped from subscriber_count if needed)
                        if 'follower_count' not in c and 'subscriber_count' in c:
                            c['follower_count'] = c['subscriber_count']
                        elif 'follower_count' not in c:
                             c['follower_count'] = 0
                             
                        # Ensure avg_views
                        if 'avg_views' not in c:
                             c['avg_views'] = c.get('metadata', {}).get('view_count', 'N/A')
                        
                        # Ensure handle is a string (required by schema)
                        if 'handle' not in c or not c['handle']:
                             c['handle'] = f"@{c['name'].lower().replace(' ', '')}"
                             
                        self.creators.append(c)
                        
                    logger.info(f"Loaded {len(self.creators)} creators from JSON fallback")
                else:
                    logger.error(f"Fallback JSON not found at {json_path}")
                    self.creators = []
            except Exception as e2:
                logger.error(f"JSON fallback failed: {e2}")
                self.creators = []
                
        return self.creators
            
        return self.creators
    
    def build_index(self):
        """
        Build FAISS index from loaded creators.
        """
        if not self.creators:
            self.load_creators()
        
        if not self.creators:
            logger.warning("Cannot build index: No creators loaded")
            return
            
        # Extract embeddings
        embeddings_list = [np.array(c['embedding'], dtype='float32') for c in self.creators]
        embeddings = np.array(embeddings_list)
        
        # Extract IDs and metadata
        creator_ids = [c['id'] for c in self.creators]
        metadata = [
            {
                'name': c['name'],
                'platform': c['platform'],
                'tags': c['tags'],
                'follower_count': c['follower_count'],
                'language': c['language'],
                'bio': c['bio'],
                'handle': c.get('handle')
            }
            for c in self.creators
        ]
        
        # Build FAISS index
        vector_store.build_index(embeddings, creator_ids, metadata)
        self.is_indexed = True
        
        logger.info(f"FAISS index built successfully with {len(self.creators)} creators")
    
    def add_creator(
        self,
        id: str,
        platform: str,
        name: str,
        handle: str,
        bio: str,
        follower_count: int,
        embedding: List[float],
        metadata: Dict[str, Any],
        content_samples: List[str],
        tags: List[str],
        niche: str,
        content_style: str
    ):
        """
        Add a new creator to the database (and JSON fallback).
        """
        creator = {
            "id": id,
            "name": name,
            "platform": platform,
            "handle": handle,
            "bio": bio,
            "follower_count": follower_count,
            "embedding": embedding,
            "metadata": metadata,
            "content_samples": content_samples,
            "tags": tags,
            "niche": niche,
            "content_style": content_style,
            "avg_views": metadata.get("view_count", "N/A"),
            "language": "en" # Default
        }
        
        # 1. Update In-Memory
        # Check if exists
        exists = False
        for i, c in enumerate(self.creators):
            if c['id'] == id:
                self.creators[i] = creator
                exists = True
                break
        
        if not exists:
            self.creators.append(creator)
            
        # 2. Save to Database (Primary)
        try:
             # Import locally to avoid circular imports
            from sqlalchemy import create_engine, text
            from sqlalchemy.orm import sessionmaker
            from app.core.config import settings
            import json as j
            
            engine = create_engine(settings.DATABASE_URL)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Check if exists in DB
            result = session.execute(text("SELECT id FROM creators WHERE id = :id"), {"id": id})
            if not result.fetchone():
                query = text("""
                    INSERT INTO creators (
                        id, platform, name, handle, bio, subscriber_count, 
                        language, niche, embedding, content_samples, tags, metadata
                    ) VALUES (
                        :id, :platform, :name, :handle, :bio, :sub_count,
                        :lang, :niche, :embedding, :samples, :tags, :meta
                    )
                """)
                
                # Format embedding for ARRAY compatible input
                embedding_val = embedding
                if isinstance(embedding, np.ndarray):
                    embedding_val = embedding.tolist()
                
                session.execute(query, {
                    "id": id,
                    "platform": platform,
                    "name": name,
                    "handle": handle,
                    "bio": bio,
                    "sub_count": follower_count,
                    "lang": "en",
                    "niche": niche,
                    "embedding": embedding_val,
                    "samples": j.dumps(content_samples),
                    "tags": j.dumps(tags),
                    "meta": j.dumps(metadata)
                })
                session.commit()
                logger.info(f"Saved creator {name} to PostgreSQL")
            session.close()
            
        except Exception as e:
            logger.error(f"Failed to save to DB: {e}")
            # Fallback to JSON is already handled below if we want, 
            # but actually the JSON block below is unconditional in my previous code?
            # Let's keep JSON as backup backup.

        # 3. Save to JSON (Persistence Fallback)
        try:
            import os
            # Save to backend root
            json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'scraped_creators.json')
            
            # Convert numpy arrays to lists for JSON
            serializable_creators = []
            for c in self.creators:
                c_copy = c.copy()
                if isinstance(c_copy['embedding'], np.ndarray):
                    c_copy['embedding'] = c_copy['embedding'].tolist()
                serializable_creators.append(c_copy)
                
            with open(json_path, 'w') as f:
                json.dump(serializable_creators, f, indent=2)
                
            logger.info(f"Saved creator {name} to JSON fallback")
            
            # Rebuild index to include new creator
            if self.is_indexed:
                self.build_index()
                
        except Exception as e:
            logger.error(f"Failed to save to JSON: {e}")

    def get_creator_by_id(self, creator_id: str) -> Dict[str, Any]:
        """Get full creator data by ID"""
        for creator in self.creators:
            if creator['id'] == creator_id:
                return creator
        return None


# Global singleton
_creator_database = None

def get_creator_database() -> CreatorDatabase:
    """Get or create global creator database"""
    global _creator_database
    if _creator_database is None:
        _creator_database = CreatorDatabase()
        # Auto-load and index on first access
        _creator_database.load_creators()
        if _creator_database.creators:
            _creator_database.build_index()
    return _creator_database


creator_database = get_creator_database()
