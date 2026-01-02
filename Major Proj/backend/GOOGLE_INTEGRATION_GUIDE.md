# Google Trends & Google News Integration Guide

## 🎉 Success! New Data Sources Added

You now have **two powerful, free data sources** that require **NO API keys**:

### ✅ Google Trends (via pytrends)
- Real-time trending data
- Interest over time metrics
- Related queries (rising & top)
- Geographic data
- Category-specific trends
- **Completely free, unlimited access**

### ✅ Google News RSS
- Latest news articles
- Topic-specific feeds
- Source attribution
- Publication timestamps
- **Completely free, no authentication**

---

## 📦 Installation

Already done! Just make sure you have:

```bash
pip install pytrends feedparser
```

---

## 🚀 Quick Start

### Using Google Trends Collector

```python
from app.services.collectors.google_trends_collector import GoogleTrendsCollector

# Initialize
collector = GoogleTrendsCollector()

# Collect trend signals
results = collector.collect_niche_signals(
    keywords=["AI", "ChatGPT", "Python", "Machine Learning"],
    niche="tech",
    timeframe='now 7-d',  # Last 7 days
    geo=''  # Worldwide (or 'US', 'GB', etc.)
)

# Access results
print(f"Trending topics: {results['trending_topics']}")
print(f"Momentum metrics: {results['momentum_metrics']}")
print(f"Currently trending: {results['trending_now']}")
```

### Using Google News Collector

```python
from app.services.collectors.google_news_collector import GoogleNewsCollector

# Initialize
collector = GoogleNewsCollector()

# Collect news signals
results = collector.collect_niche_signals(
    keywords=["artificial intelligence", "technology", "startup"],
    niche="tech_news",
    max_articles=20,
    language='en',
    country='US'
)

# Access results
print(f"Trending topics: {results['trending_topics']}")
print(f"News metrics: {results['news_metrics']}")
print(f"Recent articles: {results['recent_articles']}")
```

---

## 📊 What Data You Get

### Google Trends Response

```python
{
    "source": "google_trends",
    "niche": "tech",
    "trending_topics": [
        {
            "topic": "AI",
            "trend_direction": "rising",  # or "stable", "falling"
            "momentum_score": 0.85,
            "current_interest": 78,
            "avg_interest": 65,
            "peak_interest": 91,
            "growth_rate": 23.5,
            "rising_related_queries": ["ChatGPT", "GPT-4", "AI tools"]
        }
    ],
    "momentum_metrics": {
        "overall_momentum": 0.75,
        "avg_interest": 65,
        "peak_interest": 91,
        "trend_velocity": 0.235
    },
    "trending_now": ["Topic 1", "Topic 2", ...],
    "timestamp": "2026-01-02T03:28:06"
}
```

### Google News Response

```python
{
    "source": "google_news",
    "niche": "tech_news",
    "trending_topics": [
        {
            "topic": "artificial",
            "frequency": 15,
            "momentum_score": 0.82,
            "recency_score": 0.90,
            "article_count": 12,
            "sources": ["TechCrunch", "The Verge", "Wired"],
            "sample_headlines": ["AI breakthrough...", "New AI tool..."]
        }
    ],
    "news_metrics": {
        "total_articles": 45,
        "articles_per_keyword": 15.0,
        "unique_sources": 23,
        "coverage_velocity": 0.75,
        "recent_articles_24h": 18
    },
    "recent_articles": [...],
    "timestamp": "2026-01-02T03:28:06"
}
```

---

## 🎯 Integration with Your App

### 1. Update Signal Aggregator

You'll want to combine signals from multiple sources:

```python
# In your recommendation engine
from app.services.collectors import (
    YouTubeCollector,
    GoogleTrendsCollector,
    GoogleNewsCollector
)

def collect_all_signals(keywords, niche):
    signals = []
    
    # YouTube (requires API key)
    try:
        youtube = YouTubeCollector()
        signals.append(youtube.collect_niche_signals(keywords, niche))
    except:
        pass
    
    # Google Trends (no API key!)
    try:
        trends = GoogleTrendsCollector()
        signals.append(trends.collect_niche_signals(keywords, niche))
    except:
        pass
    
    # Google News (no API key!)
    try:
        news = GoogleNewsCollector()
        signals.append(news.collect_niche_signals(keywords, niche))
    except:
        pass
    
    return signals
```

### 2. Calculate Confidence Score

With multiple sources, you can calculate better confidence:

```python
def calculate_confidence(signals):
    """
    More sources = higher confidence
    """
    num_sources = len(signals)
    
    if num_sources >= 3:
        return "high"  # 3+ sources
    elif num_sources == 2:
        return "medium"  # 2 sources
    else:
        return "low"  # 1 source
```

### 3. Combine Trending Topics

```python
def merge_trending_topics(signals):
    """
    Merge trending topics from all sources
    """
    all_topics = {}
    
    for signal in signals:
        for topic in signal['trending_topics']:
            topic_name = topic['topic']
            
            if topic_name not in all_topics:
                all_topics[topic_name] = {
                    'name': topic_name,
                    'sources': [],
                    'total_momentum': 0,
                    'count': 0
                }
            
            all_topics[topic_name]['sources'].append(signal['source'])
            all_topics[topic_name]['total_momentum'] += topic['momentum_score']
            all_topics[topic_name]['count'] += 1
    
    # Calculate average momentum
    for topic in all_topics.values():
        topic['avg_momentum'] = topic['total_momentum'] / topic['count']
    
    # Sort by momentum
    sorted_topics = sorted(
        all_topics.values(),
        key=lambda x: x['avg_momentum'],
        reverse=True
    )
    
    return sorted_topics
```

---

## ⚡ Performance Tips

### Google Trends
- Limit to 5 keywords per request (API limitation)
- Use appropriate timeframes: `'now 1-d'`, `'now 7-d'`, `'today 1-m'`
- Cache results for at least 1 hour
- Add delays between requests (rate limiting)

### Google News
- RSS feeds are fast and reliable
- Can query multiple keywords in parallel
- No rate limits (reasonable use)
- Cache results for 15-30 minutes

---

## 🔄 Recommended Update Schedule

```python
# In your Celery tasks
from celery import Celery
from celery.schedules import crontab

app = Celery('tasks')

@app.task
def update_google_trends():
    """Update every 2 hours"""
    # Trends data changes slowly
    pass

@app.task
def update_google_news():
    """Update every 30 minutes"""
    # News is more real-time
    pass

app.conf.beat_schedule = {
    'update-trends': {
        'task': 'tasks.update_google_trends',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    'update-news': {
        'task': 'tasks.update_google_news',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}
```

---

## 🎨 Example: Complete Workflow

```python
# 1. Define your niche
niche = "tech_creators"
keywords = ["AI", "ChatGPT", "Python", "coding", "tech news"]

# 2. Collect from all sources
trends_collector = GoogleTrendsCollector()
news_collector = GoogleNewsCollector()

trends_data = trends_collector.collect_niche_signals(keywords, niche)
news_data = news_collector.collect_niche_signals(keywords, niche)

# 3. Merge and analyze
all_signals = [trends_data, news_data]
merged_topics = merge_trending_topics(all_signals)

# 4. Generate recommendation
top_topic = merged_topics[0]
confidence = "high" if len(top_topic['sources']) >= 2 else "medium"

recommendation = {
    "topic": top_topic['name'],
    "confidence": confidence,
    "momentum": top_topic['avg_momentum'],
    "sources": top_topic['sources'],
    "explanation": f"Detected across {len(top_topic['sources'])} sources with {top_topic['avg_momentum']:.0%} momentum"
}

print(recommendation)
# Output: {
#   "topic": "AI",
#   "confidence": "high",
#   "momentum": 0.85,
#   "sources": ["google_trends", "google_news"],
#   "explanation": "Detected across 2 sources with 85% momentum"
# }
```

---

## 🚨 Error Handling

Both collectors use circuit breakers (already implemented):

```python
from app.core.resilience import with_circuit_breaker

@with_circuit_breaker("google_trends")
def collect_trends():
    # Automatically handles failures
    # Opens circuit after 5 failures
    # Half-open after 60 seconds
    pass
```

---

## 📈 Next Steps

1. **Test the collectors** ✅ (Already working!)
2. **Integrate into recommendation engine**
3. **Set up Celery tasks** for periodic updates
4. **Add caching layer** (Redis)
5. **Create dashboard** to visualize trends
6. **A/B test** recommendations with users

---

## 💡 Pro Tips

1. **Combine signals**: More sources = better confidence
2. **Weight by recency**: Recent signals matter more
3. **Filter noise**: Ignore topics with low momentum
4. **Track saturation**: If everyone's posting about it, it might be too late
5. **Use geographic data**: Trends vary by region

---

## 🎉 Benefits Over Reddit API

| Feature | Reddit API | Google Trends + News |
|---------|-----------|---------------------|
| API Key Required | ✅ Yes | ❌ No |
| Rate Limits | Strict | Generous |
| Real-time Data | Delayed | Real-time |
| Global Coverage | Limited | Worldwide |
| News Integration | No | Yes |
| Trend Direction | Manual | Built-in |
| Cost | Free tier limited | Completely free |

---

## 🔗 Resources

- **pytrends docs**: https://pypi.org/project/pytrends/
- **feedparser docs**: https://pythonhosted.org/feedparser/
- **Google News RSS**: https://news.google.com/rss

---

**You're all set! 🚀 No more Reddit API issues!**
