"""
Simplified Test for Real Accounts
Tests with better error handling and output formatting
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, init_db
from app.services.scrapers.instagram_public_scraper import get_instagram_public_scraper
from app.services.intelligence.candidate_generator import CandidateGenerator
from app.models.user import User
import uuid


def test_scraper_only():
    """Test just the scraper to see what data we can get"""
    
    print("=" * 70)
    print("TESTING INSTAGRAM PUBLIC SCRAPER")
    print("=" * 70)
    
    scraper = get_instagram_public_scraper()
    
    accounts = ["that__engineer__guy", "fitgirl_08"]
    
    for account in accounts:
        print(f"\n{'=' * 70}")
        print(f"Testing: @{account}")
        print('=' * 70)
        
        try:
            # Get profile
            print(f"\n1. Fetching profile...")
            profile = scraper.get_profile(account)
            
            if profile:
                print(f"   ✅ Profile found:")
                print(f"      Name: {profile.get('full_name')}")
                print(f"      Bio: {profile.get('bio', '')[:100]}...")
                print(f"      Followers: {profile.get('follower_count'):,}")
                print(f"      Posts: {profile.get('post_count')}")
                print(f"      Verified: {profile.get('verified')}")
                print(f"      Category: {profile.get('category')}")
                print(f"      Private: {profile.get('is_private')}")
            else:
                print(f"   ❌ Profile not found")
                continue
            
            # Get posts
            print(f"\n2. Fetching recent posts...")
            time.sleep(3)  # Rate limiting
            
            posts = scraper.get_recent_posts(account, limit=10)
            
            if posts:
                print(f"   ✅ Found {len(posts)} posts")
                
                # Extract hashtags
                all_hashtags = []
                for post in posts:
                    all_hashtags.extend(post.get('hashtags', []))
                
                unique_hashtags = list(set(all_hashtags))
                print(f"      Unique hashtags: {len(unique_hashtags)}")
                if unique_hashtags:
                    print(f"      Top hashtags: {', '.join(['#' + h for h in unique_hashtags[:10]])}")
                
                # Extract mentions
                all_mentions = []
                for post in posts:
                    all_mentions.extend(post.get('mentions', []))
                
                unique_mentions = list(set(all_mentions))
                print(f"      Unique mentions: {len(unique_mentions)}")
                if unique_mentions:
                    print(f"      Mentioned accounts: {', '.join(['@' + m for m in unique_mentions[:5]])}")
            else:
                print(f"   ❌ No posts found")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"\n   Waiting 5 seconds before next account...")
        time.sleep(5)
    
    print(f"\n{'=' * 70}")
    print("SCRAPER TEST COMPLETE")
    print('=' * 70)


def test_candidate_generation():
    """Test candidate generation"""
    
    print("\n\n" + "=" * 70)
    print("TESTING CANDIDATE GENERATION")
    print("=" * 70)
    
    init_db()
    db = SessionLocal()
    
    try:
        generator = CandidateGenerator(db)
        
        accounts = ["that__engineer__guy", "fitgirl_08"]
        
        for account in accounts:
            print(f"\n{'=' * 70}")
            print(f"Generating candidates for: @{account}")
            print('=' * 70)
            
            try:
                candidates = generator.generate_candidates(
                    user_id=str(uuid.uuid4()),
                    username=account,
                    target_count=50
                )
                
                print(f"\n✅ Generated {len(candidates)} candidates:")
                for i, candidate in enumerate(candidates[:20], 1):
                    print(f"   {i}. @{candidate}")
                
                if len(candidates) > 20:
                    print(f"   ... and {len(candidates) - 20} more")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"\n   Waiting 10 seconds before next account...")
            time.sleep(10)
            
    finally:
        db.close()
    
    print(f"\n{'=' * 70}")
    print("CANDIDATE GENERATION TEST COMPLETE")
    print('=' * 70)


if __name__ == "__main__":
    # Test scraper first
    test_scraper_only()
    
    # Then test candidate generation
    test_candidate_generation()
