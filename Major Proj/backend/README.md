# Decision Assistant - Backend

Personalized daily decision assistant for social media creators.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
copy .env.example .env
```

Required API keys:
- **Reddit**: Get from https://www.reddit.com/prefs/apps
- **YouTube**: Get from https://console.cloud.google.com/apis/credentials

### 4. Setup Database

Install PostgreSQL and create a database:

```sql
CREATE DATABASE decision_assistant;
```

Update `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://username:password@localhost:5432/decision_assistant
```

### 5. Setup Redis

Install Redis or use a free tier service like Upstash.

Update `REDIS_URL` in `.env`:

```
REDIS_URL=redis://localhost:6379/0
```

## Running the Application

### Development Server

```bash
cd backend
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000

Swagger docs: http://localhost:8000/docs

### Background Workers (Celery)

```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### Celery Beat (Scheduled Tasks)

```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── resilience.py    # Circuit breakers, rate limiting
│   ├── models/              # SQLAlchemy models
│   ├── services/
│   │   ├── collectors/      # Data collectors (Reddit, YouTube, etc.)
│   │   ├── signal_health.py # Health monitoring
│   │   └── ...
│   ├── tasks/               # Celery tasks
│   └── main.py              # FastAPI app
├── requirements.txt
└── .env.example
```

## API Endpoints (Coming Soon)

- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/recommendations/daily` - Get daily recommendation
- `GET /api/niches` - List available niches
- `POST /api/feedback` - Submit recommendation feedback

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/
```

## Phase 1 Features

✅ Core backend structure
✅ Database models (User, Niche, Trend, Recommendation, SignalHealth)
✅ Resilience layer (circuit breakers, rate limiting)
✅ Reddit data collector
✅ YouTube data collector
✅ Signal health monitoring

🚧 Coming next:
- Authentication endpoints
- Recommendation generation engine
- Celery background tasks
- API endpoints for Flutter app
