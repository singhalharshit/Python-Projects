"""
Test the onboarding endpoint with detailed error output
"""
import requests
import json
import sys

def test_onboarding():
    url = "http://localhost:8000/api/onboarding/analyze"
    
    payload = {
        "user_id": "test-user-789",
        "platform": "instagram",
        "bio": "Tech enthusiast",
        "follower_count": 5000,
        "content_samples": ["Python tips", "VS Code tricks"]
    }
    
    print("Testing onboarding endpoint...", flush=True)
    print(f"Payload: {json.dumps(payload, indent=2)}", flush=True)
    print("\nSending request...", flush=True)
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"\n{'='*60}", flush=True)
        print(f"Status Code: {response.status_code}", flush=True)
        print(f"{'='*60}", flush=True)
        
        if response.status_code == 200:
            print("\n✅ SUCCESS!", flush=True)
            print("\nResponse:", flush=True)
            print(json.dumps(response.json(), indent=2), flush=True)
        else:
            print(f"\n❌ FAILED with status {response.status_code}", flush=True)
            print("\nResponse Text:", flush=True)
            print(response.text, flush=True)
            
            try:
                error_json = response.json()
                print("\nError JSON:", flush=True)
                print(json.dumps(error_json, indent=2), flush=True)
            except:
                pass
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 30 seconds", flush=True)
    except Exception as e:
        print(f"\n❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_onboarding()
