"""
Check the actual database schema for user_actions table
"""
from sqlalchemy import create_engine, inspect, text
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def check_schema():
    print("Checking database schema...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        
        # Check if user_actions table exists
        tables = inspector.get_table_names()
        print(f"\nTables in database: {tables}")
        
        if 'user_actions' in tables:
            print("\n user_actions table schema:")
            columns = inspector.get_columns('user_actions')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable={col['nullable']})")
            
            print("\n  Foreign keys:")
            fks = inspector.get_foreign_keys('user_actions')
            for fk in fks:
                print(f"  - {fk}")
        
        # Check with raw SQL
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    tc.constraint_name, 
                    tc.table_name, 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                LEFT JOIN information_schema.referential_constraints AS rc
                  ON tc.constraint_name = rc.constraint_name
                WHERE tc.table_name = 'user_actions' 
                  AND tc.constraint_type = 'FOREIGN KEY';
            """))
            
            print("\n  Detailed foreign key constraints:")
            for row in result:
                print(f"  - {dict(row)}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_schema()
