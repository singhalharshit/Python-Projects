"""
Test script for Google Trends and Google News collectors
Run this to verify the new data sources are working!
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.services.collectors.google_trends_collector import GoogleTrendsCollector
from app.services.collectors.google_news_collector import GoogleNewsCollector
import json
from datetime import datetime


def test_google_trends():
    """Test Google Trends collector"""
    print("\n" + "="*60)
    print("🔥 Testing Google Trends Collector")
    print("="*60 + "\n")
    
    collector = GoogleTrendsCollector()
    
    # Test with some trending topics
    keywords = ["AI", "ChatGPT", "Python", "Machine Learning"]
    niche = "tech"
    
    try:
        results = collector.collect_niche_signals(
            keywords=keywords,
            niche=niche,
            timeframe='now 7-d'
        )
        
        print(f"✅ Successfully collected data from Google Trends!")
        print(f"\nNiche: {results['niche']}")
        print(f"Keywords: {', '.join(results['keywords'])}")
        print(f"Timeframe: {results['timeframe']}")
        print(f"Geography: {results['geo']}")
        
        print(f"\n📊 Trending Topics ({len(results['trending_topics'])} found):")
        print("-" * 60)
        for i, topic in enumerate(results['trending_topics'][:5], 1):
            print(f"\n{i}. {topic['topic'].upper()}")
            print(f"   Trend Direction: {topic['trend_direction']} 📈" if topic['trend_direction'] == 'rising' else f"   Trend Direction: {topic['trend_direction']}")
            print(f"   Momentum Score: {topic['momentum_score']:.2f}")
            print(f"   Current Interest: {topic['current_interest']}/100")
            print(f"   Growth Rate: {topic['growth_rate']}%")
            if topic['rising_related_queries']:
                print(f"   Rising Queries: {', '.join(topic['rising_related_queries'][:3])}")
        
        print(f"\n📈 Momentum Metrics:")
        print("-" * 60)
        metrics = results['momentum_metrics']
        print(f"Overall Momentum: {metrics['overall_momentum']:.3f}")
        print(f"Average Interest: {metrics['avg_interest']}/100")
        print(f"Peak Interest: {metrics['peak_interest']}/100")
        print(f"Trend Velocity: {metrics['trend_velocity']:.3f}")
        
        if results['trending_now']:
            print(f"\n🔥 Currently Trending (Top 5):")
            print("-" * 60)
            for i, trend in enumerate(results['trending_now'][:5], 1):
                print(f"{i}. {trend}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_google_news():
    """Test Google News collector"""
    print("\n" + "="*60)
    print("📰 Testing Google News Collector")
    print("="*60 + "\n")
    
    collector = GoogleNewsCollector()
    
    # Test with some news topics
    keywords = ["artificial intelligence", "technology", "startup"]
    niche = "tech_news"
    
    try:
        results = collector.collect_niche_signals(
            keywords=keywords,
            niche=niche,
            max_articles=15
        )
        
        print(f"✅ Successfully collected data from Google News!")
        print(f"\nNiche: {results['niche']}")
        print(f"Keywords: {', '.join(results['keywords'])}")
        print(f"Total Articles: {results['total_articles_analyzed']}")
        
        print(f"\n📊 Trending Topics ({len(results['trending_topics'])} found):")
        print("-" * 60)
        for i, topic in enumerate(results['trending_topics'][:5], 1):
            print(f"\n{i}. {topic['topic'].upper()}")
            print(f"   Momentum Score: {topic['momentum_score']:.3f}")
            print(f"   Frequency: {topic['frequency']} mentions")
            print(f"   Article Count: {topic['article_count']}")
            print(f"   Recency Score: {topic['recency_score']:.3f}")
            print(f"   Sources: {', '.join(topic['sources'][:3])}")
            if topic['sample_headlines']:
                print(f"   Sample: \"{topic['sample_headlines'][0][:80]}...\"")
        
        print(f"\n📈 News Metrics:")
        print("-" * 60)
        metrics = results['news_metrics']
        print(f"Total Articles: {metrics['total_articles']}")
        print(f"Articles per Keyword: {metrics['articles_per_keyword']:.1f}")
        print(f"Unique Sources: {metrics['unique_sources']}")
        print(f"Coverage Velocity: {metrics['coverage_velocity']:.3f}")
        print(f"Recent Coverage (24h): {metrics['recent_articles_24h']} articles")
        
        print(f"\n📰 Recent Headlines (Top 3):")
        print("-" * 60)
        for i, article in enumerate(results['recent_articles'][:3], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   Source: {article['source']}")
            if article['published']:
                print(f"   Published: {article['published'].strftime('%Y-%m-%d %H:%M')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_additional_features():
    """Test additional features"""
    print("\n" + "="*60)
    print("🎯 Testing Additional Features")
    print("="*60 + "\n")
    
    # Test Google Trends suggestions
    print("🔍 Testing Google Trends Suggestions...")
    trends_collector = GoogleTrendsCollector()
    try:
        suggestions = trends_collector.get_suggestions("python programming")
        print(f"✅ Suggestions for 'python programming': {', '.join(suggestions[:5])}")
    except Exception as e:
        print(f"❌ Suggestions error: {e}")
    
    # Test Google News headlines
    print("\n📰 Testing Google News Headlines...")
    news_collector = GoogleNewsCollector()
    try:
        headlines = news_collector.get_headlines(max_headlines=5)
        print(f"✅ Top Headlines:")
        for i, headline in enumerate(headlines, 1):
            print(f"   {i}. {headline['title'][:80]}...")
    except Exception as e:
        print(f"❌ Headlines error: {e}")


if __name__ == "__main__":
    print("\n" + "🚀 " + "="*56 + " 🚀")
    print("   TESTING GOOGLE TRENDS & GOOGLE NEWS COLLECTORS")
    print("🚀 " + "="*56 + " 🚀")
    
    # Test both collectors
    trends_success = test_google_trends()
    news_success = test_google_news()
    test_additional_features()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Google Trends: {'✅ PASSED' if trends_success else '❌ FAILED'}")
    print(f"Google News: {'✅ PASSED' if news_success else '❌ FAILED'}")
    print("\n" + "="*60)
    
    if trends_success and news_success:
        print("\n🎉 All tests passed! You're ready to use these collectors!")
        print("\n💡 Next steps:")
        print("   1. Install pytrends: pip install pytrends")
        print("   2. These collectors require NO API keys!")
        print("   3. Integrate them into your recommendation engine")
        print("   4. Combine signals from multiple sources for better accuracy")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
