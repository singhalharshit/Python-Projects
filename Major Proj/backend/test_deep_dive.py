
import sys
import os
import logging
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scrapers.hybrid_instagram_scraper import get_hybrid_instagram_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deep_dive_test(username):
    print("=" * 70)
    print(f"DEEP DIVE ANALYSIS FOR: @{username}")
    print("=" * 70)

    scraper = get_hybrid_instagram_scraper()
    
    # 1. Get Profile
    print(f"\n[1] Fetching Profile Data for @{username}...")
    profile = scraper.get_profile(username)
    
    if profile:
        print("\n--- PROFILE DATA ---")
        print(f"ID: {profile.get('id')}")
        print(f"Username: {profile.get('username')}")
        print(f"Full Name: {profile.get('full_name')}")
        print(f"Bio: {profile.get('bio')}") # Bio availability is key
        print(f"Followers: {profile.get('follower_count')}")
        print(f"Following: {profile.get('following_count')}")
        print(f"Posts: {profile.get('post_count')}")
        print(f"Profile Pic: {profile.get('profile_pic_url')}")
        print("--------------------")
    else:
        print("\n[!] Failed to fetch profile data.")

    # 2. Get Posts & Signals
    print(f"\n[2] Fetching Recent Posts for @{username}...")
    posts = scraper.get_recent_posts(username, limit=5)
    
    if posts:
        print(f"\n--- RECENT POSTS ({len(posts)} found) ---")
        for i, post in enumerate(posts, 1):
            print(f"\nPost #{i}:")
            print(f"   ID: {post.get('id')}")
            print(f"   Type: {post.get('post_type')}")
            print(f"   Date: {post.get('posted_at')}")
            print(f"   Likes: {post.get('likes')}")
            print(f"   Comments: {post.get('comments')}")
            print(f"   Caption: {post.get('caption')[:100]}..." if post.get('caption') else "   Caption: [No Caption]")
            print(f"   Hashtags: {post.get('hashtags')}")
            print(f"   Mentions: {post.get('mentions')}")
        print("-----------------------")
        
        # 3. Analyze Tags
        all_hashtags = []
        for p in posts:
            all_hashtags.extend(p.get('hashtags', []))
            
        print(f"\n[3] Signal Analysis")
        print(f"Top Hashtags: {list(set(all_hashtags))[:10]}")
        
    else:
        print("\n[!] Failed to fetch posts or no posts found.")

if __name__ == "__main__":
    deep_dive_test("that__engineer__guy")
