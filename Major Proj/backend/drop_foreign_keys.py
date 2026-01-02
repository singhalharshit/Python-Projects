"""
Drop foreign key constraints from user_actions and emotional_states tables
This allows user_actions to be created without requiring a user record first
"""
import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def drop_foreign_keys():
    print("Dropping foreign key constraints...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # Drop foreign key constraint from user_actions
            print("1. Dropping foreign key from user_actions...")
            conn.execute(text("ALTER TABLE user_actions DROP CONSTRAINT IF EXISTS user_actions_user_id_fkey"))
            conn.commit()
            print("   ✓ Dropped")
            
            # Drop foreign key constraint from emotional_states
            print("2. Dropping foreign key from emotional_states...")
            conn.execute(text("ALTER TABLE emotional_states DROP CONSTRAINT IF EXISTS emotional_states_user_id_fkey"))
            conn.commit()
            print("   ✓ Dropped")
            
        print("\n✅ Foreign key constraints dropped successfully!")
        print("user_actions and emotional_states can now be created independently of users table.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    drop_foreign_keys()
