"""
Quick Validation Script
Checks that all integrations are properly connected
"""
import sys
sys.path.insert(0, 'E:\\Coding Practice\\Python Projects\\Python-Projects\\Major Proj\\backend')

def check_imports():
    """Verify all imports work"""
    print("="*60)
    print("CHECKING IMPORTS")
    print("="*60 + "\n")
    
    try:
        from app.services.decision_assistant import DecisionAssistant
        print("✅ DecisionAssistant imports successfully")
        
        from app.services.intelligence.emotional_safety_system import EmotionalSafetySystem
        print("✅ EmotionalSafetySystem imports successfully")
        
        from app.models.dynamic_niche import DynamicNiche
        print("✅ DynamicNiche model imports successfully")
        
        from app.services.intelligence.feedback_loop import FeedbackLoop
        print("✅ FeedbackLoop imports successfully")
        
        from app.api.routes.onboarding import router as onboarding_router
        print("✅ Onboarding routes import successfully")
        
        from app.api.routes.actions import router as actions_router
        print("✅ Actions routes import successfully")
        
        print("\n✅ All imports working!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_database_models():
    """Verify database models are set up"""
    print("="*60)
    print("CHECKING DATABASE MODELS")
    print("="*60 + "\n")
    
    try:
        from app.core.database import SessionLocal
        from app.models.user import User
        from app.models.dynamic_niche import DynamicNiche
        from app.models.user_action import UserAction
        from app.models.recommendation import Recommendation
        
        db = SessionLocal()
        
        # Check tables exist
        user_count = db.query(User).count()
        print(f"✅ Users table exists ({user_count} users)")
        
        niche_count = db.query(DynamicNiche).count()
        print(f"✅ DynamicNiches table exists ({niche_count} niches)")
        
        action_count = db.query(UserAction).count()
        print(f"✅ UserActions table exists ({action_count} actions)")
        
        rec_count = db.query(Recommendation).count()
        print(f"✅ Recommendations table exists ({rec_count} recommendations)")
        
        db.close()
        
        print("\n✅ All database models working!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Database check failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_api_routes():
    """Verify API routes are registered"""
    print("="*60)
    print("CHECKING API ROUTES")
    print("="*60 + "\n")
    
    try:
        from app.main import app
        
        routes = [route.path for route in app.routes]
        
        critical_routes = [
            "/api/onboarding/analyze",
            "/api/decision/daily/{user_id}",
            "/api/actions/record",
            "/api/actions/learning-insights/{user_id}"
        ]
        
        all_present = True
        for route in critical_routes:
            if route in routes:
                print(f"✅ {route}")
            else:
                print(f"❌ {route} NOT FOUND")
                all_present = False
        
        if all_present:
            print("\n✅ All critical routes registered!\n")
            return True
        else:
            print("\n⚠️  Some routes missing\n")
            return False
        
    except Exception as e:
        print(f"\n❌ Route check failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def check_integration_code():
    """Verify integration code is present"""
    print("="*60)
    print("CHECKING INTEGRATION CODE")
    print("="*60 + "\n")
    
    try:
        # Check decision_assistant.py has safety gates
        with open('E:\\Coding Practice\\Python Projects\\Python-Projects\\Major Proj\\backend\\app\\services\\decision_assistant.py', 'r') as f:
            content = f.read()
            
            if 'EmotionalSafetySystem' in content:
                print("✅ Safety gates imported in decision_assistant.py")
            else:
                print("❌ Safety gates NOT imported")
                return False
            
            if '_create_safety_override_decision' in content:
                print("✅ Safety override method present")
            else:
                print("❌ Safety override method missing")
                return False
        
        # Check onboarding.py has niche storage
        with open('E:\\Coding Practice\\Python Projects\\Python-Projects\\Major Proj\\backend\\app\\api\\routes\\onboarding.py', 'r') as f:
            content = f.read()
            
            if 'DynamicNiche' in content:
                print("✅ DynamicNiche imported in onboarding.py")
            else:
                print("❌ DynamicNiche NOT imported")
                return False
            
            if 'dynamic_niche.member_count' in content:
                print("✅ Niche storage logic present")
            else:
                print("❌ Niche storage logic missing")
                return False
        
        # Check actions.py has feedback loop
        with open('E:\\Coding Practice\\Python Projects\\Python-Projects\\Major Proj\\backend\\app\\api\\routes\\actions.py', 'r') as f:
            content = f.read()
            
            if 'FeedbackLoop' in content:
                print("✅ FeedbackLoop imported in actions.py")
            else:
                print("❌ FeedbackLoop NOT imported")
                return False
            
            if 'learning-insights' in content:
                print("✅ Learning insights endpoint present")
            else:
                print("❌ Learning insights endpoint missing")
                return False
        
        print("\n✅ All integration code present!\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Code check failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation checks"""
    print("\n" + "="*60)
    print("  INTEGRATION VALIDATION")
    print("="*60 + "\n")
    
    results = []
    
    # Check 1: Imports
    results.append(("Imports", check_imports()))
    
    # Check 2: Database Models
    results.append(("Database Models", check_database_models()))
    
    # Check 3: API Routes
    results.append(("API Routes", check_api_routes()))
    
    # Check 4: Integration Code
    results.append(("Integration Code", check_integration_code()))
    
    # Summary
    print("="*60)
    print("  VALIDATION SUMMARY")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*60}")
    print(f"  {passed}/{total} checks passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED! 🎉")
        print("\n✅ Integrations are properly connected")
        print("✅ Ready to run integration tests")
        print("\nNext step: python test_integrations.py\n")
        return True
    else:
        print("⚠️  Some validations failed")
        print("\nPlease check the errors above and fix them.\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
