"""
Test Instagram Scraper with Real Accounts
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    from app.services.instagram_scraper import get_instagram_scraper
    
    scraper = get_instagram_scraper()
    
    if not scraper.available:
        print("❌ Instaloader not available!")
        print("Install it: pip install instaloader")
        sys.exit(1)
    
    print("🧪 Testing Instagram Scraper...")
    print("="*60)
    
    # Test with well-known accounts
    test_accounts = [
        'instagram',  # Instagram's official account
        'cristiano',  # Cristiano Ronaldo (most followed)
        'therock',    # Dwayne Johnson
        'that_engineer_guy',  # Your account
    ]
    
    for username in test_accounts:
        print(f"\n📍 Testing: @{username}")
        print("-"*60)
        
        try:
            profile = scraper.get_profile(username)
            
            if profile:
                print(f"✅ SUCCESS!")
                print(f"   Name: {profile.get('full_name')}")
                print(f"   Followers: {profile.get('followers'):,}")
                print(f"   Posts: {profile.get('posts')}")
                print(f"   Verified: {profile.get('is_verified')}")
            else:
                print(f"❌ FAILED: Could not fetch profile")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "="*60)
    print("Test complete!")
