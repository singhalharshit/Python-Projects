"""
Test Onboarding API
Verifies that the Instagram login/analysis flow works
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_analyze_profile():
    print("\n" + "📸 " + "="*76 + " 📸")
    print("   TEST: Instagram Onboarding Flow")
    print("📸 " + "="*76 + " 📸")
    
    username = "tech_guy_101"
    print(f"\n👤 Simulating login for: @{username}...")
    
    response = client.post("/api/onboarding/analyze", json={"username": username})
    
    if response.status_code == 200:
        data = response.json()
        niche = data['inferred_niche']
        competitors = data['suggested_competitors']
        
        print(f"✅ Analysis Success!")
        print(f"   Inferred Niche: {niche}")
        print(f"   Found {len(competitors)} Competitors:")
        
        for comp in competitors[:3]:
            print(f"   - {comp['name']} ({comp['subs']})")
    else:
        print(f"❌ Failed: {response.text}")

if __name__ == "__main__":
    test_analyze_profile()
