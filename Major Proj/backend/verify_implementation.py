import sys
import os
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.getcwd())

def verify_imports():
    print("Verifying imports...")
    try:
        from app.api.routes import onboarding, decision, actions, competitors, recommendations
        print("✅ API Routes imported successfully")
        
        from app.models import DynamicNiche, TopicHistory, UserAction, EmotionalState, UserCompetitor
        print("✅ Models imported successfully")
        
        from app.services.decision_assistant import DecisionAssistant
        print("✅ DecisionAssistant imported successfully")
        
        from app.services.intelligence.niche_discovery import NicheDiscoveryEngine
        from app.services.intelligence.opportunity_detector import OpportunityDetector
        from app.services.intelligence.competitor_discovery import CompetitorDiscoveryEngine
        print("✅ Intelligence Engines imported successfully")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)

def verify_decision_assistant():
    print("\nVerifying DecisionAssistant initialization...")
    try:
        from app.services.decision_assistant import DecisionAssistant
        
        db = MagicMock()
        assistant = DecisionAssistant(db)
        print("✅ DecisionAssistant initialized successfully")
        
    except Exception as e:
        print(f"❌ DecisionAssistant Logic Error: {e}")
        sys.exit(1)

def verify_schemas():
    print("\nVerifying Schemas...")
    try:
        from app.api.routes.onboarding import ProfileData
        # Test optional platform
        data = ProfileData(user_id="test_user")
        assert data.platform == "instagram"
        print("✅ ProfileData schema handles missing platform correctly")
    except Exception as e:
        print(f"❌ Schema Verification Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_imports()
    verify_schemas()
    verify_decision_assistant()
    print("\n🎉 Verification Passed!")
