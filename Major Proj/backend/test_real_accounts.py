"""
Test Creator Similarity Engine with Real Accounts
Tests discovery for @that__engineer__guy and @fitgirl_08
"""
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.services.intelligence.competitor_discovery_orchestrator import CompetitorDiscoveryOrchestrator
from app.models.user import User
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_accounts():
    """Test discovery for real Instagram accounts"""
    
    print("=" * 70)
    print("TESTING CREATOR SIMILARITY ENGINE - REAL ACCOUNTS")
    print("=" * 70)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Create or get test user
        print("\n2. Getting/Creating test user...")
        existing_user = db.query(User).filter(User.email == "test_real@example.com").first()
        
        if existing_user:
            print(f"   User already exists: {existing_user.id}")
            test_user = existing_user
        else:
            test_user = User(
                id=uuid.uuid4(),
                email="test_real@example.com",
                password_hash="dummy_hash"
            )
            db.add(test_user)
            db.commit()
            print(f"   Created user: {test_user.id}")
        
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        # Test 1: @that__engineer__guy
        print("\n" + "=" * 70)
        print("TEST 1: @that__engineer__guy")
        print("=" * 70)
        
        try:
            competitors1 = orchestrator.discover_competitors(
                user_id=str(test_user.id),
                username="that__engineer__guy",
                limit=12
            )
            
            print(f"\n[SUCCESS] Found {len(competitors1)} competitors for @that__engineer__guy:")
            print()
            
            for i, comp in enumerate(competitors1[:10], 1):
                print(f"{i}. @{comp.get('username', 'N/A')}")
                print(f"   Score: {comp.get('score', 0):.3f}")
                print(f"   Reason: {comp.get('match_reason', 'N/A')}")
                
                # Show top 3 signals
                signals = comp.get('signals', {})
                valid_signals = [(k, v) for k, v in signals.items() if v is not None and v > 0.3]
                valid_signals.sort(key=lambda x: x[1], reverse=True)
                
                if valid_signals:
                    print(f"   Top signals:")
                    for signal_name, signal_value in valid_signals[:3]:
                        print(f"     - {signal_name}: {signal_value:.3f}")
                print()
                
        except Exception as e:
            print(f"[ERROR] Error testing @that__engineer__guy: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: @fitgirl_08
        print("\n" + "=" * 70)
        print("TEST 2: @fitgirl_08")
        print("=" * 70)
        
        try:
            competitors2 = orchestrator.discover_competitors(
                user_id=str(test_user.id),
                username="fitgirl_08",
                limit=12
            )
            
            print(f"\n[SUCCESS] Found {len(competitors2)} competitors for @fitgirl_08:")
            print()
            
            for i, comp in enumerate(competitors2[:10], 1):
                print(f"{i}. @{comp.get('username', 'N/A')}")
                print(f"   Score: {comp.get('score', 0):.3f}")
                print(f"   Reason: {comp.get('match_reason', 'N/A')}")
                
                # Show top 3 signals
                signals = comp.get('signals', {})
                valid_signals = [(k, v) for k, v in signals.items() if v is not None and v > 0.3]
                valid_signals.sort(key=lambda x: x[1], reverse=True)
                
                if valid_signals:
                    print(f"   Top signals:")
                    for signal_name, signal_value in valid_signals[:3]:
                        print(f"     - {signal_name}: {signal_value:.3f}")
                print()
                
        except Exception as e:
            print(f"[ERROR] Error testing @fitgirl_08: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("TESTING COMPLETE")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[FATAL] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_real_accounts()
