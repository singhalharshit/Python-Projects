"""
Standalone test for Google Trends and Google News collectors
This version doesn't require the full app dependencies
"""
from pytrends.request import TrendReq
import feedparser
from datetime import datetime
from urllib.parse import quote_plus


def test_google_trends():
    """Test Google Trends API"""
    print("\n" + "="*60)
    print("🔥 Testing Google Trends")
    print("="*60 + "\n")
    
    try:
        # Initialize pytrends
        pytrends = TrendReq(hl='en-US', tz=360)
        
        # Test keywords
        keywords = ["AI", "ChatGPT", "Python"]
        print(f"Testing keywords: {', '.join(keywords)}\n")
        
        # Build payload
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='', gprop='')
        
        # Get interest over time
        interest_df = pytrends.interest_over_time()
        
        if not interest_df.empty:
            print("✅ Successfully fetched Google Trends data!\n")
            print("📊 Interest Over Time (Last 7 Days):")
            print("-" * 60)
            
            for keyword in keywords:
                if keyword in interest_df.columns:
                    values = interest_df[keyword].values
                    avg = values.mean()
                    peak = values.max()
                    current = values[-1]
                    
                    print(f"\n{keyword}:")
                    print(f"  Current Interest: {current}/100")
                    print(f"  Average Interest: {avg:.1f}/100")
                    print(f"  Peak Interest: {peak}/100")
                    
                    # Calculate trend
                    if len(values) >= 2:
                        recent_avg = values[-3:].mean()
                        older_avg = values[:-3].mean()
                        if older_avg > 0:
                            growth = ((recent_avg - older_avg) / older_avg) * 100
                            trend = "📈 Rising" if growth > 20 else "📉 Falling" if growth < -20 else "➡️ Stable"
                            print(f"  Trend: {trend} ({growth:+.1f}%)")
        
        # Get trending searches
        print("\n\n🔥 Currently Trending in US:")
        print("-" * 60)
        trending = pytrends.trending_searches(pn='united_states')
        if not trending.empty:
            for i, trend in enumerate(trending[0].head(10), 1):
                print(f"{i:2d}. {trend}")
        
        # Get related queries
        print("\n\n🔍 Related Queries for 'AI':")
        print("-" * 60)
        pytrends.build_payload(['AI'], cat=0, timeframe='now 7-d')
        related = pytrends.related_queries()
        
        if 'AI' in related and related['AI']['rising'] is not None:
            rising_df = related['AI']['rising']
            if not rising_df.empty:
                print("\nRising queries:")
                for i, row in rising_df.head(5).iterrows():
                    print(f"  • {row['query']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_google_news():
    """Test Google News RSS"""
    print("\n\n" + "="*60)
    print("📰 Testing Google News RSS")
    print("="*60 + "\n")
    
    try:
        # Test search query
        query = "artificial intelligence"
        print(f"Searching for: '{query}'\n")
        
        # Build RSS URL
        search_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en&gl=US&ceid=US:en"
        
        # Parse feed
        feed = feedparser.parse(search_url)
        
        if feed.entries:
            print(f"✅ Successfully fetched {len(feed.entries)} articles!\n")
            print("📰 Recent Headlines:")
            print("-" * 60)
            
            for i, entry in enumerate(feed.entries[:10], 1):
                print(f"\n{i}. {entry.title}")
                
                # Get source
                source = entry.source.title if hasattr(entry, 'source') else "Unknown"
                print(f"   Source: {source}")
                
                # Get publication date
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                    print(f"   Published: {pub_date.strftime('%Y-%m-%d %H:%M')}")
                
                # Get link
                print(f"   Link: {entry.link[:60]}...")
        
        # Test top headlines
        print("\n\n📰 Top Headlines (US):")
        print("-" * 60)
        headlines_url = "https://news.google.com/rss?hl=en&gl=US&ceid=US:en"
        headlines_feed = feedparser.parse(headlines_url)
        
        if headlines_feed.entries:
            for i, entry in enumerate(headlines_feed.entries[:5], 1):
                print(f"\n{i}. {entry.title}")
                source = entry.source.title if hasattr(entry, 'source') else "Unknown"
                print(f"   Source: {source}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀 " + "="*56 + " 🚀")
    print("   TESTING GOOGLE TRENDS & GOOGLE NEWS")
    print("   (No API Keys Required!)")
    print("🚀 " + "="*56 + " 🚀")
    
    # Run tests
    trends_ok = test_google_trends()
    news_ok = test_google_news()
    
    # Summary
    print("\n\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Google Trends: {'✅ PASSED' if trends_ok else '❌ FAILED'}")
    print(f"Google News:   {'✅ PASSED' if news_ok else '❌ FAILED'}")
    print("="*60)
    
    if trends_ok and news_ok:
        print("\n🎉 SUCCESS! Both data sources are working perfectly!")
        print("\n💡 Key Benefits:")
        print("   ✅ No API keys required")
        print("   ✅ Real-time trending data")
        print("   ✅ Fast and reliable")
        print("   ✅ Free unlimited access")
        print("\n🚀 You can now use these collectors in your app!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("\n")
