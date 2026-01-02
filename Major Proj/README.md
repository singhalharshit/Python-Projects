# Decision Assistant for Social Media Creators

> **"Someone sensible is watching my back"** — A protective shield against algorithmic guesswork

Personalized daily decision assistant that tells creators exactly what to post, when to post it, what to avoid, and why—before they create anything.

## 🎯 Core Philosophy

- **Trust over features** - Conservative explanations, visible uncertainty
- **Clarity over sophistication** - One clear action per day
- **Resilience over optimization** - Graceful degradation, multi-signal architecture

## 🚀 Features


### Phase 1 (Current)
- ✅ Multi-signal trend detection (Google Trends + Google News + YouTube)
- ✅ No API keys required for primary sources (Google Trends & News)
- ✅ Graceful degradation with confidence scoring
- ✅ Circuit breakers and rate limiting
- ✅ Signal health monitoring
- 🚧 User authentication
- 🚧 Daily recommendation generation
- 🚧 Flutter mobile app


### Future Phases
- Anti-trend detection (saturation alerts)
- Vibe analysis (hype vs. critique vs. calm)
- Multi-niche support
- "Don't post today" recommendations
- Peer benchmarking (anonymized)
- Draft feedback

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App                          │
│              (iOS / Android / Web)                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Resilience Layer (Circuit Breakers, Rate Limit) │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Data Collectors (Reddit, YouTube, RSS, etc.)    │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Recommendation Engine + Confidence Scoring      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│         PostgreSQL + Redis + Celery Workers             │
└─────────────────────────────────────────────────────────┘
```

## 📦 Tech Stack

- **Backend**: Python + FastAPI + SQLAlchemy
- **Database**: PostgreSQL + Redis
- **Background Jobs**: Celery
- **Frontend**: Flutter (iOS, Android, Web)
- **Data Sources**: Free-tier APIs (Reddit, YouTube, GitHub, HN, RSS)

## 🛠️ Setup

### Backend Setup

See [backend/README.md](backend/README.md) for detailed instructions.

Quick start:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Configure .env with your API keys
uvicorn app.main:app --reload
```

### Frontend Setup (Coming Soon)

```bash
cd frontend
flutter pub get
flutter run
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and resilience patterns
- [Implementation Plan](docs/implementation_plan.md) - Detailed development roadmap
- [API Documentation](http://localhost:8000/docs) - Swagger UI (when running)

## 🔑 API Keys

### Primary Sources (No API Keys Required!) 🎉

1. **Google Trends** ✅
   - No setup needed
   - Just install: `pip install pytrends`
   - Real-time trending data

2. **Google News** ✅
   - No setup needed
   - Uses public RSS feeds
   - Latest news coverage

### Optional Sources (API Keys Optional)

3. **YouTube Data API v3** (Optional)
   - Go to https://console.cloud.google.com/apis/credentials
   - Create project and enable YouTube Data API v3
   - Create API key
   - Free tier: 10,000 requests/day

4. **Reddit API** (Optional)
   - Go to https://www.reddit.com/prefs/apps
   - Create an app (script type)
   - Get client ID and secret
   - Free tier: 60 requests/minute

   - Create project and enable YouTube Data API v3
   - Create API key

## 🎨 Design Principles

### Conservative Explanations
❌ "You should definitely post about X"  
✅ "Signals suggest early momentum around X"

❌ "This will get 47% more engagement"  
✅ "Based on 5/7 signals (high confidence)"

### Graceful Degradation
- System works with 3/7 data sources active
- Lower confidence instead of failure
- Transparent signal health status

### Calm User Experience
- One clear action per day
- Visible uncertainty (confidence scores)
- "Don't post today" when appropriate
- Minimal notifications

## 📊 Project Status

**Phase 1: Core Foundation** (Weeks 1-2) - 60% Complete

- [x] Backend structure
- [x] Database models
- [x] Resilience layer
- [x] Reddit collector
- [x] YouTube collector
- [x] Signal health monitoring
- [ ] Authentication
- [ ] Recommendation engine
- [ ] Flutter app basics

## 🤝 Contributing

This is a learning project. Contributions welcome!

## 📝 License

MIT License - See LICENSE file for details

---

**Built with calm certainty, not clever complexity** 🧘‍♂️