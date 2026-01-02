"""
Final System Verification
Tests that the API is up and serving dynamic creators
"""
import requests
import json
import time
import sys

# Wait for server to start
print("Waiting for server...")
time.sleep(5)

try:
    # Test Analyze Profile Endpoint
    print("\n1. Testing /analyze endpoint (getting suggestions)...")
    resp = requests.post(
        'http://127.0.0.1:8000/api/onboarding/analyze',
        json={'username': 'code_learner', 'user_id': 'verify_test'}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"   ✓ Success! Got {len(data.get('suggested_competitors', []))} suggestions")
        
        # Check if we got real scraped creators
        creators = data['suggested_competitors']
        if creators:
            print(f"   Top suggestion: {creators[0]['name']}")
            print(f"   Tags: {creators[0]['tags']}")
            print(f"   Confidence: {creators[0]['confidence_score']}%")
            
            # Verify it's not a mock creator
            if 'youtube' in creators[0].get('platform', '').lower() or 'programming' in str(creators[0].get('tags')):
                print("   ✓ Verified: Dynamic YouTube data is being served!")
            else:
                print("   ? Warning: Data might be from fallback/mock?")
    else:
        print(f"   ❌ Failed: {resp.status_code} - {resp.text}")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\nVerification Complete")
