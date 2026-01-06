# 🔑 API KEYS SETUP GUIDE

This guide helps you get API keys for real competitor discovery.

---

## Required APIs

1. ✅ **YouTube Data API** (Recommended - FREE)
2. ✅ **Reddit API** (Recommended - FREE)
3. ⚠️ **SerpAPI / Google Search** (Optional - Paid after free tier)

---

## 1. YouTube Data API (FREE)

### Why You Need It
- Search for YouTube channels
- Find content creators in specific niches
- Discover similar accounts

### Setup Steps (5 minutes)

#### Step 1: Go to Google Cloud Console
https://console.cloud.google.com/

#### Step 2: Create New Project
1. Click "Select a project" → "New Project"
2. Name: "Decision Assistant"
3. Click "Create"

#### Step 3: Enable YouTube Data API
1. Go to "APIs & Services" → "Library"
2. Search for "YouTube Data API v3"
3. Click "Enable"

#### Step 4: Create API Key
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. (Optional) Click "Restrict Key" → Select "YouTube Data API v3"

#### Step 5: Add to .env
```bash
YOUTUBE_API_KEY=your_api_key_here
```

### Quota Limits
- **FREE**: 10,000 units/day
- **Search**: ~100 units per request
- **You get**: ~100 searches/day (plenty!)

---

## 2. Reddit API (FREE)

### Why You Need It
- Find creator mentions in subreddits
- Discover trending topics
- See community discussions

### Setup Steps (5 minutes)

#### Step 1: Create Reddit Account
https://www.reddit.com/ (if you don't have one)

#### Step 2: Go to App Preferences
https://www.reddit.com/prefs/apps

#### Step 3: Create App
1. Scroll to bottom
2. Click "Create another app..."
3. Fill in:
   - **Name**: Decision Assistant
   - **Type**: Script
   - **Description**: Competitor discovery
   - **About URL**: (leave blank)
   - **Redirect URI**: http://localhost:8000
4. Click "Create app"

#### Step 4: Get Credentials
You'll see:
- **Client ID**: (under the app name, small text)
- **Secret**: (labeled "secret")

#### Step 5: Add to .env
```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
```

### Quota Limits
- **FREE**: 60 requests/minute
- **You get**: Plenty for discovery!

---

## 3. SerpAPI / Google Search (OPTIONAL)

### Why You Need It
- Search Google for creator content
- Find blog mentions
- Discover trending topics

### Option A: SerpAPI (Easier)

#### Setup Steps (3 minutes)
1. Go to: https://serpapi.com/
2. Sign up for free account
3. Get API key from dashboard
4. Add to .env:
```bash
SERPAPI_KEY=your_api_key_here
```

#### Pricing
- **FREE**: 100 searches/month
- **Paid**: $50/month for 5,000 searches

### Option B: Skip It
- System works without Google search
- YouTube + Reddit are usually enough
- Can add later if needed

---

## 📝 Complete .env File

After getting API keys, your `.env` should look like:

```bash
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/decision_assistant

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# YouTube API (Required for real discovery)
YOUTUBE_API_KEY=AIzaSyC-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Reddit API (Required for community discovery)
REDDIT_CLIENT_ID=xxxxxxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# SerpAPI (Optional - for Google search)
SERPAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# JWT Secret
SECRET_KEY=your-secret-key-here
```

---

## 🧪 Test Your API Keys

### Test Script
Create `test_apis.py`:

```python
import os
from dotenv import load_dotenv
from app.services.web_search_service import get_web_search_service

load_dotenv()

web_search = get_web_search_service()

print("\n🧪 Testing API Keys...\n")
print("="*60)

# Test YouTube
print("\n1. Testing YouTube API...")
youtube_results = web_search.search_youtube("fitness workouts")
print(f"   ✅ Found {len(youtube_results)} YouTube results")

# Test Reddit
print("\n2. Testing Reddit API...")
reddit_results = web_search.search_reddit("fitness creators")
print(f"   ✅ Found {len(reddit_results)} Reddit results")

# Test Google (if available)
print("\n3. Testing Google Search...")
google_results = web_search.search_google("fitness influencers instagram")
print(f"   ✅ Found {len(google_results)} Google results")

print("\n" + "="*60)
print("🎉 All APIs working!\n")
```

### Run Test
```bash
cd backend
python test_apis.py
```

---

## ⚠️ Without API Keys

If you don't set up API keys:
- ✅ System still works
- ⚠️ Uses demo/fallback data
- ⚠️ Limited competitor discovery
- ⚠️ Not production-ready

**For MVP/Testing**: Demo data is fine
**For Production**: Get real API keys

---

## 🚀 Quick Start (Just Copy-Paste)

### 1. Get YouTube Key (5 min)
```
1. Go to: https://console.cloud.google.com/
2. Create project
3. Enable "YouTube Data API v3"
4. Create API key
5. Add to .env: YOUTUBE_API_KEY=xxx
```

### 2. Get Reddit Keys (5 min)
```
1. Go to: https://www.reddit.com/prefs/apps
2. Create app (type: Script)
3. Copy client_id and secret
4. Add to .env:
   REDDIT_CLIENT_ID=xxx
   REDDIT_CLIENT_SECRET=xxx
```

### 3. Restart Backend
```bash
cd backend
python run_backend.py
```

### 4. Test
```bash
# Frontend: Enter username with bio/hashtags
# Backend: Will use real APIs!
```

---

## 💡 Cost Breakdown

### FREE Tier (Recommended for MVP)
- YouTube: 10,000 units/day = ~100 searches
- Reddit: 60 requests/minute = plenty
- **Total Cost**: $0/month

### With Google Search (Optional)
- SerpAPI: 100 searches/month free
- After that: $50/month
- **Total Cost**: $0-50/month

### For 1,000 Users
- YouTube: Still free (within quota)
- Reddit: Still free
- SerpAPI: ~$50-100/month
- **Total Cost**: ~$50-100/month

---

## 🎯 Priority

### Must Have (for real discovery):
1. ✅ YouTube API
2. ✅ Reddit API

### Nice to Have:
3. ⚠️ SerpAPI / Google Search

### Can Skip:
4. ❌ Instagram Graph API (we use semantic discovery instead)

---

## ❓ FAQ

**Q: Do I need all three APIs?**
A: No. YouTube + Reddit are enough for MVP.

**Q: What if I don't set any keys?**
A: System uses demo data (works but limited).

**Q: Are these APIs free forever?**
A: YouTube & Reddit have generous free tiers. Google search costs money after 100 searches/month.

**Q: Can I use my own API keys?**
A: Yes! Just add them to `.env`

**Q: Will this work in production?**
A: Yes, with proper rate limiting and caching.

---

## ✅ Done!

Once you have API keys:
1. Add to `.env`
2. Restart backend
3. Test with real username
4. Real competitors discovered! 🎉

---

**Next**: Test the system with real API keys and see semantic discovery in action!
