"""
Quick Database Fix - Add Missing Columns
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from app.core.database import engine
    
    print("🔧 Adding missing columns to dynamic_niches table...")
    
    # SQL statements to add columns
    sql_statements = [
        "ALTER TABLE dynamic_niches ADD COLUMN IF NOT EXISTS name TEXT;",
        "ALTER TABLE dynamic_niches ADD COLUMN IF NOT EXISTS embedding_centroid JSON;",
        "ALTER TABLE dynamic_niches ADD COLUMN IF NOT EXISTS descriptors JSON;",
        "ALTER TABLE dynamic_niches ADD COLUMN IF NOT EXISTS is_micro INTEGER DEFAULT 0;",
        "ALTER TABLE dynamic_niches ADD COLUMN IF NOT EXISTS member_count INTEGER DEFAULT 0;",
        
        # Copy data from existing columns
        "UPDATE dynamic_niches SET name = label WHERE name IS NULL;",
        "UPDATE dynamic_niches SET embedding_centroid = centroid_vector WHERE embedding_centroid IS NULL;",
        "UPDATE dynamic_niches SET descriptors = keywords WHERE descriptors IS NULL;",
        "UPDATE dynamic_niches SET member_count = creator_count WHERE member_count = 0;",
    ]
    
    try:
        with engine.connect() as conn:
            for sql in sql_statements:
                print(f"  Executing: {sql[:60]}...")
                conn.execute(sql)
                conn.commit()
        
        print("\n✅ Database updated successfully!")
        print("\nYou can now restart the backend with: python run_backend.py")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        print("\nTrying SQLite-specific syntax...")
        
        # Try SQLite syntax (no IF NOT EXISTS)
        sqlite_statements = [
            "ALTER TABLE dynamic_niches ADD COLUMN name TEXT;",
            "ALTER TABLE dynamic_niches ADD COLUMN embedding_centroid TEXT;",
            "ALTER TABLE dynamic_niches ADD COLUMN descriptors TEXT;",
            "ALTER TABLE dynamic_niches ADD COLUMN is_micro INTEGER DEFAULT 0;",
            "ALTER TABLE dynamic_niches ADD COLUMN member_count INTEGER DEFAULT 0;",
        ]
        
        with engine.connect() as conn:
            for sql in sqlite_statements:
                try:
                    print(f"  Executing: {sql[:60]}...")
                    conn.execute(sql)
                    conn.commit()
                except Exception as inner_e:
                    if "duplicate column" in str(inner_e).lower():
                        print(f"    ⚠️  Column already exists, skipping...")
                    else:
                        print(f"    ❌ Error: {inner_e}")
            
            # Copy data
            try:
                conn.execute("UPDATE dynamic_niches SET name = label WHERE name IS NULL;")
                conn.execute("UPDATE dynamic_niches SET embedding_centroid = centroid_vector WHERE embedding_centroid IS NULL;")
                conn.execute("UPDATE dynamic_niches SET descriptors = keywords WHERE descriptors IS NULL;")
                conn.execute("UPDATE dynamic_niches SET member_count = creator_count WHERE member_count = 0;")
                conn.commit()
                print("\n✅ Database updated successfully!")
            except Exception as copy_error:
                print(f"⚠️  Data copy warning: {copy_error}")
                print("✅ Columns added, you can restart the backend")
