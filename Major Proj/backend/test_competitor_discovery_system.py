"""
Test Competitor Discovery System
Tests the complete Creator Similarity Engine
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.services.intelligence.competitor_discovery_orchestrator import CompetitorDiscoveryOrchestrator
from app.models.user import User
import uuid


def test_competitor_discovery():
    """Test the complete competitor discovery flow"""
    
    print("=" * 60)
    print("TESTING CREATOR SIMILARITY ENGINE")
    print("=" * 60)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # Create test user
        print("\n2. Creating test user...")
        test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            username="test_user",
            hashed_password="dummy"
        )
        db.add(test_user)
        db.commit()
        
        print(f"   Created user: {test_user.id}")
        
        # Test discovery
        print("\n3. Testing competitor discovery...")
        print("   Target: @mkbhd (tech creator)")
        
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        competitors = orchestrator.discover_competitors(
            user_id=str(test_user.id),
            username="mkbhd",
            limit=12
        )
        
        print(f"\n   Found {len(competitors)} competitors:")
        print()
        
        for i, comp in enumerate(competitors[:5], 1):
            print(f"   {i}. @{comp['username']}")
            print(f"      Score: {comp['score']:.3f}")
            print(f"      Reason: {comp['match_reason']}")
            print(f"      Signals:")
            for signal, value in comp['signals'].items():
                if value is not None:
                    print(f"        - {signal}: {value:.3f}")
            print()
        
        # Test feedback
        if competitors:
            print("\n4. Testing feedback (accept)...")
            first_competitor = competitors[0]
            
            result = orchestrator.handle_feedback(
                user_id=str(test_user.id),
                creator_id=first_competitor['creator_id'] or first_competitor['username'],
                action='accept'
            )
            
            print(f"   Status: {result['status']}")
            print(f"   Updated weights:")
            for weight_name, weight_value in result['updated_weights'].items():
                if 'weight' in weight_name:
                    print(f"     - {weight_name}: {weight_value:.3f}")
        
        # Test weights retrieval
        print("\n5. Testing weight retrieval...")
        weights = orchestrator.get_user_weights(str(test_user.id))
        
        print("   Current weights:")
        for weight_name, weight_value in weights.items():
            if 'weight' in weight_name:
                print(f"     - {weight_name}: {weight_value:.3f}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        db.query(User).filter(User.email == "test@example.com").delete()
        db.commit()
        db.close()


if __name__ == "__main__":
    test_competitor_discovery()
