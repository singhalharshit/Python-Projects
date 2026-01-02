"""
Quick Database Fix - Add Missing Columns (PostgreSQL)
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from app.core.database import engine
    from sqlalchemy import text
    
    print("🔧 Adding missing columns to dynamic_niches table (PostgreSQL)...")
    
    # PostgreSQL SQL statements
    sql_statements = [
        # Add columns with IF NOT EXISTS (PostgreSQL 9.6+)
        """
        DO $$ 
        BEGIN 
            BEGIN
                ALTER TABLE dynamic_niches ADD COLUMN name TEXT;
            EXCEPTION
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'column name already exists';
            END;
        END $$;
        """,
        
        """
        DO $$ 
        BEGIN 
            BEGIN
                ALTER TABLE dynamic_niches ADD COLUMN embedding_centroid JSON;
            EXCEPTION
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'column embedding_centroid already exists';
            END;
        END $$;
        """,
        
        """
        DO $$ 
        BEGIN 
            BEGIN
                ALTER TABLE dynamic_niches ADD COLUMN descriptors JSON;
            EXCEPTION
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'column descriptors already exists';
            END;
        END $$;
        """,
        
        """
        DO $$ 
        BEGIN 
            BEGIN
                ALTER TABLE dynamic_niches ADD COLUMN is_micro INTEGER DEFAULT 0;
            EXCEPTION
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'column is_micro already exists';
            END;
        END $$;
        """,
        
        """
        DO $$ 
        BEGIN 
            BEGIN
                ALTER TABLE dynamic_niches ADD COLUMN member_count INTEGER DEFAULT 0;
            EXCEPTION
                WHEN duplicate_column THEN 
                    RAISE NOTICE 'column member_count already exists';
            END;
        END $$;
        """,
        
        # Copy data from existing columns
        "UPDATE dynamic_niches SET name = label WHERE name IS NULL;",
        "UPDATE dynamic_niches SET embedding_centroid = centroid_vector WHERE embedding_centroid IS NULL;",
        "UPDATE dynamic_niches SET descriptors = keywords WHERE descriptors IS NULL;",
        "UPDATE dynamic_niches SET member_count = creator_count WHERE member_count = 0 OR member_count IS NULL;",
    ]
    
    try:
        with engine.connect() as conn:
            for i, sql in enumerate(sql_statements, 1):
                print(f"  [{i}/{len(sql_statements)}] Executing SQL...")
                conn.execute(text(sql))
                conn.commit()
        
        print("\n✅ Database updated successfully!")
        print("\nColumns added to dynamic_niches table:")
        print("  - name")
        print("  - embedding_centroid")
        print("  - descriptors")
        print("  - is_micro")
        print("  - member_count")
        print("\n✅ You can now restart the backend with: python run_backend.py")
        
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
