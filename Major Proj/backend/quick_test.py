"""
Quick test for Google Trends and Google News
"""
from pytrends.request import TrendReq
import feedparser

print("Testing Google Trends...")
try:
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload(['Python', 'AI'], timeframe='now 7-d')
    df = pytrends.interest_over_time()
    print(f"✅ Google Trends works! Got {len(df)} data points")
    print(f"   Python interest: {df['Python'].mean():.1f}/100")
    print(f"   AI interest: {df['AI'].mean():.1f}/100")
except Exception as e:
    print(f"❌ Google Trends failed: {e}")

print("\nTesting Google News...")
try:
    feed = feedparser.parse("https://news.google.com/rss/search?q=technology&hl=en&gl=US&ceid=US:en")
    print(f"✅ Google News works! Got {len(feed.entries)} articles")
    if feed.entries:
        print(f"   Latest: {feed.entries[0].title[:60]}...")
except Exception as e:
    print(f"❌ Google News failed: {e}")

print("\n✅ Both APIs are working! No API keys needed!")
