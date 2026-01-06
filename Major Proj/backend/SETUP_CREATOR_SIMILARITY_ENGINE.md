# Creator Similarity Engine - Setup Guide

## Quick Start

### 1. Database Migration

Create and run the database migration:

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Add Creator Similarity Engine models"

# Review the migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### 2. Register API Routes

Update `app/main.py` to include the new routes:

```python
# Add this import
from app.api.routes import competitors_v2

# Add this router registration (after other routers)
app.include_router(
    competitors_v2.router, 
    prefix="/api/competitors/v2", 
    tags=["competitors-v2"]
)
```

### 3. Test the System

Run the test script:

```bash
cd backend
python test_competitor_discovery_system.py
```

Expected output:
```
==============================================================
TESTING CREATOR SIMILARITY ENGINE
==============================================================

1. Initializing database...
2. Creating test user...
   Created user: <uuid>
3. Testing competitor discovery...
   Target: @mkbhd (tech creator)
   
   Found 12 competitors:
   
   1. @unboxtherapy
      Score: 0.847
      Reason: Similar content themes and style
      Signals:
        - content_similarity: 0.820
        - hashtag_overlap: 0.750
        ...

✅ ALL TESTS PASSED
==============================================================
```

### 4. Start the Backend

```bash
cd backend
python run_backend.py
```

Or:

```bash
uvicorn app.main:app --reload
```

### 5. Test API Endpoints

Using curl or Postman:

```bash
# Discover competitors
curl -X POST http://localhost:8000/api/competitors/v2/discover \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "instagram_handle": "mkbhd",
    "limit": 12
  }'

# Accept a competitor
curl -X POST http://localhost:8000/api/competitors/v2/{creator_id}/accept \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get learned weights
curl -X GET http://localhost:8000/api/competitors/v2/weights \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Files Created

### Database Models (4)
- ✅ `app/models/creator_post.py`
- ✅ `app/models/competitor_candidate.py`
- ✅ `app/models/user_competitor_feedback.py`
- ✅ `app/models/user_preference_weights.py`

### Services (5)
- ✅ `app/services/scrapers/instagram_public_scraper.py`
- ✅ `app/services/intelligence/candidate_generator.py`
- ✅ `app/services/intelligence/competitor_scorer.py`
- ✅ `app/services/intelligence/competitor_preference_learner.py`
- ✅ `app/services/intelligence/competitor_discovery_orchestrator.py`

### API Routes (1)
- ✅ `app/api/routes/competitors_v2.py`

### Tests (1)
- ✅ `test_competitor_discovery_system.py`

### Documentation (1)
- ✅ `CREATOR_SIMILARITY_ENGINE.md`

## Troubleshooting

### Issue: "Circuit breaker open"

**Cause:** Too many failed Instagram requests

**Solution:**
- Wait 5-10 minutes
- Check internet connection
- Verify Instagram is accessible

### Issue: "No candidates generated"

**Cause:** User has no posts or private account

**Solution:**
- Ensure target account is public
- Ensure target account has posts
- Try a different account

### Issue: "Module not found"

**Cause:** Missing dependencies

**Solution:**
```bash
pip install -r requirements.txt
```

## Next Steps

1. ✅ Run database migration
2. ✅ Register API routes
3. ✅ Test the system
4. ✅ Deploy to production

## Support

For issues or questions, refer to:
- [`CREATOR_SIMILARITY_ENGINE.md`](CREATOR_SIMILARITY_ENGINE.md) - Full documentation
- [`walkthrough.md`](walkthrough.md) - Implementation details
- [`implementation_plan.md`](implementation_plan.md) - Architecture design

---

**Ready to discover competitors!** 🚀
