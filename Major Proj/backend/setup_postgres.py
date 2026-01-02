
import sys
import os
import json
import numpy as np
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Force UTF-8 for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.database import Base, engine as app_engine

# Override settings just for this script if needed, or rely on what's loaded
# Since .env might not be readable/writable by me, we rely on user having set it or defaults
# But user provided specific credentials just now: postgres:12345678
DB_USER = "postgres"
DB_PASS = "12345678"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "decision_assistant"

def create_database():
    print(f"1. Connecting to PostgreSQL at {DB_HOST}...")
    try:
        # Connect to default 'postgres' database to create the new one
        con = psycopg2.connect(
            user=DB_USER, 
            password=DB_PASS, 
            host=DB_HOST, 
            port=DB_PORT, 
            dbname="postgres"
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # Check if exists
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"   Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print("   Database created.")
        else:
            print(f"   Database '{DB_NAME}' already exists.")
            
        cursor.close()
        con.close()
        return True
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def setup_schema():
    print("2. Setting up Schema & Extensions...")
    # Connection string for the specific DB
    db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(db_url)
        # Skip pgvector extension - we use FAISS for search
        # with engine.connect() as conn:
        #     conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        #     conn.commit()
            
        # Create tables using SQLAlchemy models
        print("   Creating tables...")
        
        # DROP table to ensure fresh schema (since we changed Vector -> Array)
        with engine.connect() as conn:
            print("   Dropping old 'creators' table if exists...")
            conn.execute(text("DROP TABLE IF EXISTS creators"))
            conn.commit()
            
        from app.models.creator import Creator  # Import to register with Base
        # We need to bind the app's Base to this new engine
        Base.metadata.create_all(bind=engine)
        print("   Tables created.")
        return True
    except Exception as e:
        print(f"❌ Error setting up schema: {e}")
        return False

def import_json_data():
    print("3. Importing content from scraped_creators.json...")
    json_path = 'scraped_creators.json'
    if not os.path.exists(json_path):
        print("   No JSON file found to import.")
        return

    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        print(f"   Loaded {len(data)} items from JSON.")
            
        db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        Session = sessionmaker(bind=create_engine(db_url))
        session = Session()
        
        # Create tables using SQLAlchemy models is done in setup_schema, 
        # but importing Creator here ensures it's known? No, using raw SQL.
        
        count = 0
        for item in data:
            # Check exist
            exists = session.execute(
                text("SELECT id FROM creators WHERE id = :id"), 
                {"id": item['id']}
            ).fetchone()
            
            if exists:
                print(f"   Skipping {item['id']} (already exists)")
                continue
            
            print(f"   Inserting {item.get('name')}...")
                
            # Prepare data
            embedding_val = item['embedding']
            embedding_pg = embedding_val
            
            if isinstance(embedding_val, list):
                # Convert list to Postgres array literal format: {1.0,2.0,...}
                # Ensure all items are strings first
                floats = [str(f) for f in embedding_val]
                embedding_pg = "{" + ",".join(floats) + "}"
            
            # Serialize JSON fields
            import json as j
            
            query = text("""
                INSERT INTO creators (
                    id, platform, name, handle, bio, subscriber_count, 
                    language, niche, embedding, content_samples, tags, metadata
                ) VALUES (
                    :id, :platform, :name, :handle, :bio, :sub_count,
                    :lang, :niche, :embedding, :samples, :tags, :meta
                )
            """)
            
            session.execute(query, {
                "id": item['id'],
                "platform": item['platform'],
                "name": item['name'],
                "handle": item.get('handle'),
                "bio": item['bio'],
                "sub_count": item.get('follower_count', 0),
                "lang": item.get('language', 'en'),
                "niche": item.get('niche', 'general'),
                "embedding": embedding_pg, # Correct PG format
                "samples": j.dumps(item.get('content_samples', [])),
                "tags": j.dumps(item.get('tags', [])),
                "meta": j.dumps(item.get('metadata', {}))
            })
            count += 1
            
        session.commit()
        print(f"   Imported {count} creators from JSON.")
        
        # Verify
        result = session.execute(text("SELECT COUNT(*) FROM creators"))
        final_count = result.scalar()
        print(f"   VERIFICATION: Table now has {final_count} rows.")
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")

if __name__ == "__main__":
    if create_database():
        if setup_schema():
            import_json_data()
            print("\n✅ Migration Complete! Update your .env file with:")
            print(f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
