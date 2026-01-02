"""
Test the onboarding endpoint and save full output to file
"""
import requests
import json
import sys

def test_onboarding():
    url = "http://localhost:8000/api/onboarding/analyze"
    
    payload = {
        "user_id": "test-user-999",
        "platform": "instagram",
        "bio": "Tech enthusiast",
        "follower_count": 5000,
        "content_samples": ["Python tips", "VS Code tricks"]
    }
    
    output_lines = []
    output_lines.append("Testing onboarding endpoint...")
    output_lines.append(f"Payload: {json.dumps(payload, indent=2)}")
    output_lines.append("\nSending request...")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        output_lines.append(f"\n{'='*60}")
        output_lines.append(f"Status Code: {response.status_code}")
        output_lines.append(f"{'='*60}")
        
        if response.status_code == 200:
            output_lines.append("\n✅ SUCCESS!")
            output_lines.append("\nResponse:")
            output_lines.append(json.dumps(response.json(), indent=2))
        else:
            output_lines.append(f"\n❌ FAILED with status {response.status_code}")
            output_lines.append("\nResponse Text:")
            output_lines.append(response.text)
            
            try:
                error_json = response.json()
                output_lines.append("\nError JSON:")
                output_lines.append(json.dumps(error_json, indent=2))
            except:
                pass
                
    except requests.exceptions.Timeout:
        output_lines.append("❌ Request timed out after 30 seconds")
    except Exception as e:
        output_lines.append(f"\n❌ Error: {e}")
        import traceback
        output_lines.append(traceback.format_exc())
    
    # Write to file
    full_output = "\n".join(output_lines)
    with open("test_output.txt", "w", encoding="utf-8") as f:
        f.write(full_output)
    
    # Also print to console
    print(full_output)

if __name__ == "__main__":
    test_onboarding()
