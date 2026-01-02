"""
Integration Test Suite
Tests all critical integrations implemented
"""
import asyncio
import sys
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add app to path
sys.path.insert(0, 'E:\\Coding Practice\\Python Projects\\Python-Projects\\Major Proj\\backend')

from app.core.database import SessionLocal, init_db
from app.models.user import User
from app.models.user_action import UserAction
from app.models.recommendation import Recommendation
from app.services.decision_assistant import DecisionAssistant
from app.services.intelligence.emotional_safety_system import EmotionalSafetySystem
from app.services.intelligence.emotional_tracker import EmotionalStateTracker


def print_test_header(test_name: str):
    """Print a nice test header"""
    print(f"\n{'='*60}")
    print(f"  TEST: {test_name}")
    print(f"{'='*60}\n")


def print_result(passed: bool, message: str):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {message}\n")


async def test_safety_gates():
    """Test 1: Safety Gates Integration"""
    print_test_header("Safety Gates Integration")
    
    db = SessionLocal()
    try:
        # Create test user
        test_user = User(
            id='test_safety_user_123',
            email='safety@test.com',
            password_hash='fake_hash'
        )
        
        # Check if user exists
        existing = db.query(User).filter_by(id=test_user.id).first()
        if existing:
            db.delete(existing)
            db.commit()
        
        db.add(test_user)
        db.commit()
        
        print("Created test user")
        
        # Simulate burnout scenario (8 consecutive days of posting)
        print("Simulating burnout scenario (8 consecutive days)...")
        for i in range(8):
            action = UserAction(
                user_id=test_user.id,
                recommendation_id=f'rec_{i}',
                action_type='followed',
                timestamp=datetime.utcnow() - timedelta(days=7-i),
                context={}
            )
            db.add(action)
        
        db.commit()
        print(f"Created {8} consecutive posting actions")
        
        # Test safety gates
        tracker = EmotionalStateTracker(db)
        safety_system = EmotionalSafetySystem(db, tracker)
        
        safety_check = safety_system.check_safety_gates(
            user_id=test_user.id,
            proposed_action='post'
        )
        
        # Validate results
        passed = True
        
        if not safety_check:
            print_result(False, "Safety system returned no result")
            passed = False
        else:
            print(f"Safety check result:")
            print(f"  - Safe: {safety_check.get('safe')}")
            print(f"  - Override action: {safety_check.get('override_action')}")
            print(f"  - Severity: {safety_check.get('severity')}")
            print(f"  - Gates triggered: {len(safety_check.get('gates_triggered', []))}")
            
            # Should NOT be safe (burnout detected)
            if safety_check.get('safe'):
                print_result(False, "Expected safety override, but system said safe")
                passed = False
            elif safety_check.get('override_action') != 'rest':
                print_result(False, f"Expected 'rest', got '{safety_check.get('override_action')}'")
                passed = False
            else:
                print_result(True, "Safety gates correctly detected burnout and suggested rest")
        
        # Cleanup
        db.delete(test_user)
        db.query(UserAction).filter_by(user_id=test_user.id).delete()
        db.commit()
        
        return passed
        
    except Exception as e:
        print_result(False, f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_dynamic_niche_storage():
    """Test 2: Dynamic Niche Storage"""
    print_test_header("Dynamic Niche Storage")
    
    db = SessionLocal()
    try:
        from app.models.dynamic_niche import DynamicNiche
        
        # Create test user
        test_user = User(
            id='test_niche_user_456',
            email='niche@test.com',
            password_hash='fake_hash'
        )
        
        # Cleanup existing
        existing = db.query(User).filter_by(id=test_user.id).first()
        if existing:
            db.delete(existing)
        
        db.add(test_user)
        db.commit()
        
        print("Created test user")
        
        # Test onboarding with niche discovery
        assistant = DecisionAssistant(db)
        
        profile_data = {
            'platform': 'instagram',
            'bio': 'AI and machine learning content creator passionate about deep learning',
            'follower_count': 1000
        }
        
        content_samples = [
            'Introduction to neural networks and deep learning',
            'Python for data science and ML',
            'Latest trends in artificial intelligence'
        ]
        
        print("Running onboarding...")
        result = await assistant.onboard_creator(
            user_id=test_user.id,
            profile_data=profile_data,
            content_samples=content_samples
        )
        
        print(f"Onboarding complete:")
        print(f"  - User ID: {result.get('user_id')}")
        print(f"  - Niche: {result.get('niche', {}).get('label', 'None')}")
        print(f"  - Competitors found: {len(result.get('competitors', []))}")
        
        # Check if niche was stored
        if result.get('niche'):
            niche_id = result['niche']['niche_id']
            
            # Query database for niche
            stored_niche = db.query(DynamicNiche).filter_by(id=niche_id).first()
            
            if stored_niche:
                print(f"\n✓ Niche stored in database:")
                print(f"  - ID: {stored_niche.id}")
                print(f"  - Name: {stored_niche.name}")
                print(f"  - Members: {stored_niche.member_count}")
                print(f"  - Is Micro: {stored_niche.is_micro}")
                
                # Check if user is linked
                db.refresh(test_user)
                if test_user.niche_id == niche_id:
                    print_result(True, "User successfully linked to dynamic niche")
                    passed = True
                else:
                    print_result(False, f"User not linked (niche_id: {test_user.niche_id})")
                    passed = False
            else:
                print_result(False, "Niche not found in database")
                passed = False
        else:
            print_result(False, "No niche discovered during onboarding")
            passed = False
        
        # Cleanup
        if result.get('niche'):
            niche_id = result['niche']['niche_id']
            db.query(DynamicNiche).filter_by(id=niche_id).delete()
        
        db.delete(test_user)
        db.commit()
        
        return passed
        
    except Exception as e:
        print_result(False, f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_feedback_loop():
    """Test 3: Enhanced Feedback Loop"""
    print_test_header("Enhanced Feedback Loop")
    
    db = SessionLocal()
    try:
        from app.services.intelligence.feedback_loop import FeedbackLoop
        from app.services.intelligence.preference_learner import PreferenceLearner
        from app.services.intelligence.embedding_service import EmbeddingService
        
        # Create test user and recommendation
        test_user = User(
            id='test_feedback_user_789',
            email='feedback@test.com',
            password_hash='fake_hash'
        )
        
        # Cleanup existing
        existing = db.query(User).filter_by(id=test_user.id).first()
        if existing:
            db.delete(existing)
        
        db.add(test_user)
        db.commit()
        
        print("Created test user")
        
        # Create test recommendation
        test_rec = Recommendation(
            id='test_rec_feedback_123',
            user_id=test_user.id,
            date=datetime.utcnow().date(),
            topic='Test AI Topic',
            reasoning='Test reasoning',
            confidence_score=0.75,
            action='post'
        )
        db.add(test_rec)
        db.commit()
        
        print("Created test recommendation")
        
        # Initialize feedback loop
        feedback_loop = FeedbackLoop(
            db=db,
            preference_learner=PreferenceLearner(db),
            embedding_service=EmbeddingService()
        )
        
        print("Processing 'followed' action...")
        
        # Process action
        await feedback_loop.process_user_action(
            user_id=test_user.id,
            recommendation_id=test_rec.id,
            action='followed',
            timestamp=datetime.utcnow(),
            context={'time_spent': 120, 'platform': 'web'}
        )
        
        # Check if action was recorded
        action = db.query(UserAction).filter_by(
            user_id=test_user.id,
            recommendation_id=test_rec.id
        ).first()
        
        if action:
            print(f"\n✓ Action recorded:")
            print(f"  - Type: {action.action_type}")
            print(f"  - Timestamp: {action.timestamp}")
            print(f"  - Context: {action.context}")
            
            # Check if recommendation was updated
            db.refresh(test_rec)
            if test_rec.was_accepted:
                print(f"\n✓ Recommendation marked as accepted")
                print_result(True, "Feedback loop successfully processed action")
                passed = True
            else:
                print_result(False, "Recommendation not marked as accepted")
                passed = False
        else:
            print_result(False, "Action not recorded in database")
            passed = False
        
        # Cleanup
        db.delete(test_user)
        db.delete(test_rec)
        if action:
            db.delete(action)
        db.commit()
        
        return passed
        
    except Exception as e:
        print_result(False, f"Exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*60)
    print("  INTEGRATION TEST SUITE")
    print("  Testing Critical Integrations")
    print("="*60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    
    results = []
    
    # Test 1: Safety Gates
    result1 = await test_safety_gates()
    results.append(("Safety Gates", result1))
    
    # Test 2: Dynamic Niche Storage
    result2 = await test_dynamic_niche_storage()
    results.append(("Dynamic Niche Storage", result2))
    
    # Test 3: Feedback Loop
    result3 = await test_feedback_loop()
    results.append(("Feedback Loop", result3))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60 + "\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  TOTAL: {passed_count}/{total_count} tests passed")
    print(f"{'='*60}\n")
    
    if passed_count == total_count:
        print("🎉 ALL INTEGRATIONS WORKING! 🎉\n")
        return True
    else:
        print("⚠️  Some integrations need fixes\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
