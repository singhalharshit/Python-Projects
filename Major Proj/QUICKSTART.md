# Quick Start Guide

## Prerequisites

- Python 3.9+
- PostgreSQL
- Redis

## Quick Setup (Windows)

```powershell
cd backend
.\setup.ps1
```

This will:
- Create virtual environment
- Install dependencies
- Create .env file from template

## Manual Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```env
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@localhost:5432/decision_assistant

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Secret (generate a random string)
SECRET_KEY=your-super-secret-key-change-this

# Reddit API (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# YouTube API (get from https://console.cloud.google.com/apis/credentials)
YOUTUBE_API_KEY=your_api_key
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

Server will start at: http://localhost:8000

API Documentation: http://localhost:8000/docs

## Testing the API

### 1. Create a User

```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "selected_niches": ["AI-dev creators"]
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Get User Profile

```bash
curl -X GET "http://localhost:8000/api/users/profile" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   └── users.py         # User management
│   │   └── schemas.py           # Pydantic schemas
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── auth.py              # JWT utilities
│   │   └── resilience.py        # Circuit breakers
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py
│   │   ├── niche.py
│   │   ├── trend.py
│   │   ├── recommendation.py
│   │   └── signal_health.py
│   ├── services/
│   │   ├── collectors/          # Data collectors
│   │   │   ├── reddit_collector.py
│   │   │   └── youtube_collector.py
│   │   └── signal_health.py     # Health monitoring
│   └── main.py                  # FastAPI app
├── requirements.txt
├── .env.example
└── setup.ps1
```

## Available Endpoints

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Get current user

### Users
- `GET /api/users/profile` - Get profile
- `PUT /api/users/profile` - Update profile
- `GET /api/users/niches` - List niches
- `POST /api/users/niches/{id}/select` - Select niche
- `DELETE /api/users/niches/{id}/unselect` - Unselect niche

### System
- `GET /` - API info
- `GET /health` - Health check

## Next Steps

- [ ] Set up PostgreSQL database
- [ ] Set up Redis
- [ ] Get API keys (Reddit, YouTube)
- [ ] Configure .env file
- [ ] Run the server
- [ ] Test endpoints using Swagger UI (http://localhost:8000/docs)

## Troubleshooting

### Database Connection Error

Make sure PostgreSQL is running and DATABASE_URL is correct:

```bash
# Create database
psql -U postgres
CREATE DATABASE decision_assistant;
```

### Redis Connection Error

Make sure Redis is running:

```bash
# Windows (if using Redis for Windows)
redis-server
```

### Import Errors

Make sure virtual environment is activated and dependencies are installed:

```bash
venv\Scripts\activate
pip install -r requirements.txt
```
