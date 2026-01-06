"""
Test API Keys
Quick test to verify all API integrations are working
"""
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from dotenv import load_dotenv
load_dotenv()

print("\n🧪 TESTING API INTEGRATIONS")
print("="*60)

from app.services.web_search_service import get_web_search_service

web_search = get_web_search_service()

# Test YouTube
print("\n1️⃣  Testing YouTube API...")
print("-"*60)
try:
    youtube_results = web_search.search_youtube("fitness workouts", max_results=3)
    if youtube_results:
        print(f"   ✅ SUCCESS: Found {len(youtube_results)} YouTube channels")
        if youtube_results[0].get('creator_name'):
            print(f"   📺 Example: {youtube_results[0]['creator_name']}")
        if web_search.youtube_available:
            print("   🔑 Using REAL YouTube API")
        else:
            print("   ⚠️  Using demo data (set YOUTUBE_API_KEY to use real API)")
    else:
        print("   ❌ FAILED: No results returned")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test Reddit
print("\n2️⃣  Testing Reddit API...")
print("-"*60)
try:
    reddit_results = web_search.search_reddit("fitness creators", limit=3)
    if reddit_results:
        print(f"   ✅ SUCCESS: Found {len(reddit_results)} Reddit posts")
        if reddit_results[0].get('creator_name'):
            print(f"   💬 Example: {reddit_results[0]['creator_name']}")
        if web_search.reddit_available:
            print("   🔑 Using REAL Reddit API")
        else:
            print("   ⚠️  Using demo data (set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)")
    else:
        print("   ❌ FAILED: No results returned")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test Google Search
print("\n3️⃣  Testing Google Search...")
print("-"*60)
try:
    google_results = web_search.search_google("fitness influencers instagram", num_results=3)
    if google_results:
        print(f"   ✅ SUCCESS: Found {len(google_results)} Google results")
        if google_results[0].get('title'):
            print(f"   🔍 Example: {google_results[0]['title'][:50]}...")
        if web_search.google_available:
            print("   🔑 Using REAL Google API (SerpAPI)")
        else:
            print("   ⚠️  Using demo data (set SERPAPI_KEY to use real API)")
    else:
        print("   ❌ FAILED: No results returned")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Summary
print("\n" + "="*60)
print("📊 SUMMARY")
print("="*60)

apis_working = 0
apis_total = 3

if web_search.youtube_available:
    print("✅ YouTube API: CONFIGURED")
    apis_working += 1
else:
    print("⚠️  YouTube API: Using demo data")

if web_search.reddit_available:
    print("✅ Reddit API: CONFIGURED")
    apis_working += 1
else:
    print("⚠️  Reddit API: Using demo data")

if web_search.google_available:
    print("✅ Google Search: CONFIGURED")
    apis_working += 1
else:
    print("⚠️  Google Search: Using demo data (optional)")

print("\n" + "="*60)

if apis_working >= 2:
    print("🎉 READY FOR PRODUCTION!")
    print(f"   {apis_working}/{apis_total} APIs configured")
elif apis_working >= 1:
    print("✅ READY FOR TESTING!")
    print(f"   {apis_working}/{apis_total} APIs configured")
    print("   Tip: Add more API keys for better results")
else:
    print("⚠️  USING DEMO DATA")
    print("   Add API keys for real competitor discovery")
    print("   See: API_KEYS_SETUP.md")

print("="*60)
print()
