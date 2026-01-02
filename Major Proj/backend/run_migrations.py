"""
Run Database Migrations
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from alembic.config import Config
    from alembic import command
    
    print("🔧 Running database migrations...")
    
    # Load alembic config
    alembic_cfg = Config("alembic.ini")
    
    try:
        # Run upgrade
        command.upgrade(alembic_cfg, "head")
        print("\n✅ Migrations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
