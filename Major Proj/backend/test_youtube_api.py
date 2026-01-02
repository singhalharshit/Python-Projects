"""
Test YouTube API Integration
Run this after adding YOUTUBE_API_KEY to .env
"""
import sys
sys.path.append('e:/Coding Practice/Python Projects/Python-Projects/Major Proj/backend')

from app.services.intelligence.youtube_scraper import youtube_scraper
import json

print("=" * 60)
print("YOUTUBE API TEST")
print("=" * 60)

# Check if API is initialized
if not youtube_scraper.youtube:
    print("\n❌ YouTube API not initialized!")
    print("Please add YOUTUBE_API_KEY to .env file")
    print("\nHow to get API key:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create project → Enable YouTube Data API v3")
    print("3. Create credentials → API Key")
    print("4. Add to .env: YOUTUBE_API_KEY=your_key_here")
    sys.exit(1)

print("\n✓ YouTube API initialized")

# Test 1: Search for tech channels
print("\n" + "=" * 60)
print("TEST 1: Search for Programming Channels")
print("=" * 60)

channels = youtube_scraper.search_channels("programming tutorials", max_results=5)

if channels:
    print(f"\n✓ Found {len(channels)} channels:")
    for i, channel in enumerate(channels, 1):
        print(f"\n{i}. {channel['title']}")
        print(f"   ID: {channel['id']}")
        print(f"   Description: {channel['description'][:100]}...")
else:
    print("\n❌ No channels found")

# Test 2: Get channel details
if channels:
    print("\n" + "=" * 60)
    print("TEST 2: Get Channel Details")
    print("=" * 60)
    
    channel_id = channels[0]['id']
    details = youtube_scraper.get_channel_details(channel_id)
    
    if details:
        print(f"\n✓ Channel Details:")
        print(f"   Name: {details['name']}")
        print(f"   Subscribers: {details['subscriber_count']:,}")
        print(f"   Videos: {details['video_count']:,}")
        print(f"   Views: {details['view_count']:,}")
        print(f"   Country: {details.get('country', 'N/A')}")
    else:
        print("\n❌ Failed to get channel details")

# Test 3: Get recent videos
if channels:
    print("\n" + "=" * 60)
    print("TEST 3: Get Recent Videos")
    print("=" * 60)
    
    videos = youtube_scraper.get_recent_videos(channel_id, max_results=5)
    
    if videos:
        print(f"\n✓ Found {len(videos)} recent videos:")
        for i, video in enumerate(videos, 1):
            print(f"\n{i}. {video['title']}")
            print(f"   Published: {video['published_at']}")
    else:
        print("\n❌ No videos found")

# Test 4: Extract content corpus
if channels and details and videos:
    print("\n" + "=" * 60)
    print("TEST 4: Extract Content Corpus")
    print("=" * 60)
    
    corpus = youtube_scraper.extract_content_corpus(details, videos)
    print(f"\n✓ Corpus length: {len(corpus)} characters")
    print(f"   Preview: {corpus[:200]}...")

# Quota status
print("\n" + "=" * 60)
print("QUOTA STATUS")
print("=" * 60)

quota = youtube_scraper.get_quota_status()
print(f"\nUsed: {quota['used']} / {quota['limit']} units")
print(f"Remaining: {quota['remaining']} units")

print("\n" + "=" * 60)
print("TEST COMPLETE!")
print("=" * 60)
