
import asyncio
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.instagram.playwright_client import PlaywrightClient
from app.services.instagram.candidate_generator import PlaywrightCandidateGenerator

async def test_discovery():
    print("="*60)
    print("TESTING PLAYWRIGHT COMPETITOR DISCOVERY")
    print("="*60)
    
    # Check for auth file
    auth_file = "instagram_auth.json"
    if not os.path.exists(auth_file):
        print(f"❌ WARNING: {auth_file} not found!")
        print("The test will run in ANONYMOUS mode (might fail/redirect).")
        print("Please run 'python setup_instagram_auth.py' first for best results.")
    else:
        print(f"✅ Found auth file: {auth_file}")

    client = PlaywrightClient(headless=True) # Run headless for test
    generator = PlaywrightCandidateGenerator(client)
    
    hashtags = ['coding', 'python', 'developer']
    print(f"\n🔍 Testing discovery for hashtags: {hashtags}")
    
    try:
        await client.start()
        
        candidates = await generator.generate(hashtags, limit_per_tag=5)
        
        print("\n" + "="*60)
        print(f"RESULTS: Found {len(candidates)} unique candidates")
        print("="*60)
        
        for i, username in enumerate(candidates, 1):
            print(f"{i}. {username}")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(test_discovery())
