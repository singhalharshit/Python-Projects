
import os
import sys
import json
from sqlalchemy import text
from app.core.database import SessionLocal

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_read():
    print("Connecting via SessionLocal...")
    from app.core.config import settings
    # Safe print
    url = str(settings.DATABASE_URL)
    masked_url = url.split('@')[-1] if '@' in url else "NO_CREDENTIALS"
    print(f"DEBUG: Connecting to {masked_url}")
    
    try:
        db = SessionLocal()
        # Verify DB name
        res = db.execute(text("SELECT current_database()"))
        print(f"Connected to DB: {res.scalar()}")
        
        print("Fetching creators...")
        result = db.execute(text("SELECT * FROM creators"))
        rows = result.fetchall()
        print(f"Found {len(rows)} rows.")
        
        if len(rows) > 0:
            row = rows[0]
            print(f"Sample row: {row.name}")
            print(f"Embedding type: {type(row.embedding)}")
            print(f"Embedding val (preview): {str(row.embedding)[:50]}")
            
            # Simulate the parsing logic in creator_database.py
            embedding = row.embedding
            if isinstance(embedding, str):
                try:
                    loaded = json.loads(embedding)
                    print("Parsed via json.loads: SUCCESS")
                except Exception as e:
                    print(f"Parsed via json.loads: FAILED ({e})")
                    # Try manual parse if it's Postgres array string
                    if embedding.startswith('{') and embedding.endswith('}'):
                        print("Detected Postgres Array String format")
        
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_read()
