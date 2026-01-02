import requests
import json

# Test the ML API
resp = requests.post(
    'http://127.0.0.1:8000/api/onboarding/analyze',
    json={'username': 'that_engineer_guy', 'user_id': 'test456'}
)

data = resp.json()
print('Username:', data['username'])
print('Niche:', data['inferred_niche'])
print('\nTop Suggestions:')
for i, c in enumerate(data['suggested_competitors'][:5], 1):
    print(f"{i}. {c['name']} - {c['confidence_score']}% match")
    print(f"   Tags: {', '.join(c['tags'][:4])}")
    print(f"   Reason: {c['match_reason']}")
    print()
