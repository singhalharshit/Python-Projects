
import requests
import json
import sys

try:
    print("Testing API at http://localhost:8000/api/onboarding/analyze")
    response = requests.post(
        "http://localhost:8000/api/onboarding/analyze",
        json={"username": "aliabdaal", "user_id": "test_user"},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response.status_code}")
    print("Headers:", response.headers)
    
    try:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
        
        # Validate critical fields
        if "suggested_competitors" in data:
            for i, comp in enumerate(data["suggested_competitors"]):
                print(f"Suggestion {i} Handle: {comp.get('handle')} (Type: {type(comp.get('handle'))})")
                if comp.get('handle') is None:
                    print("ERROR: Handle is None!")
    except Exception as e:
        print("Could not parse JSON:", response.text)
        
except Exception as e:
    print(f"Request Failed: {e}")
