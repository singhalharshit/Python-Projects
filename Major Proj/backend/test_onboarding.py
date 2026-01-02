"""
Test the onboarding endpoint to verify the fixes
"""
import requests
import json

def test_onboarding():
    url = "http://localhost:8000/api/onboarding/analyze"
    
    payload = {
        "user_id": "test-user-456",
        "platform": "instagram",
        "bio": "Tech enthusiast sharing coding tips and tutorials",
        "follower_count": 5000,
        "content_samples": [
            "How to learn Python in 2024",
            "Best VS Code extensions for productivity"
        ]
    }
    
    print("Testing onboarding endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nSending request...")
    
    try:
        response = requests.post(url, json=payload)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            print("\nResponse:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ FAILED with status {response.status_code}")
            print("\nResponse:")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onboarding()
