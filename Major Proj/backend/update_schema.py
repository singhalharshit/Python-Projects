"""
Update database schema to fix user_actions table
Changes:
1. Drop and recreate user_actions table with Text type for content_vector
2. This fixes the JSON truncation issue
"""
import sys
import os
from sqlalchemy import create_engine, text

# Add parent to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def update_schema():
    print("Updating database schema...")
    
    try:
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            print("1. Dropping old user_actions table...")
            conn.execute(text("DROP TABLE IF EXISTS user_actions CASCADE"))
            conn.commit()
            print("   ✓ Table dropped")
            
            print("2. Dropping old emotional_states table...")
            conn.execute(text("DROP TABLE IF EXISTS emotional_states CASCADE"))
            conn.commit()
            print("   ✓ Table dropped")
            
            print("3. Recreating tables with updated schema...")
            # Import models to register with Base
            from app.core.database import Base
            from app.models.user_action import UserAction, EmotionalState
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            print("   ✓ Tables recreated")
            
        print("\n✅ Schema update complete!")
        print("The user_actions table now uses Text type for content_vector.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error updating schema: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_schema()
