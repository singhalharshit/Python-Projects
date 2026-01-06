# Creator Similarity Engine

## Overview

The **Creator Similarity Engine** discovers competing creators who compete for the same audience attention. It uses ethical public data scraping, multi-signal heuristics, and continuous learning from user feedback.

### Key Features

- ✅ **Ethical Scraping** - Only public data, no login required
- ✅ **Multi-Signal Scoring** - 6 different signals combined
- ✅ **Learning Loop** - Improves with every user interaction
- ✅ **Graceful Degradation** - Works even when signals are missing
- ✅ **Small Creator Discovery** - Finds creators of all sizes

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer                             │
│  /discover, /accept, /reject, /weights, /suggestions    │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│          CompetitorDiscoveryOrchestrator                │
│  (Coordinates candidate generation, scoring, learning)  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────────┐  ┌──────────────┐
│  Candidate   │  │   Competitor     │  │  Preference  │
│  Generator   │  │     Scorer       │  │   Learner    │
└──────────────┘  └──────────────────┘  └──────────────┘
        │                   │                   │
        ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────┐
│            Instagram Public Scraper                     │
│  (Ethical scraping with rate limiting & caching)        │
└─────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Candidate Generation (Multi-Path Discovery)

The system generates 50-200 raw candidates using multiple discovery paths:

**Path A - Hashtag Exploration:**
- Extract top hashtags from user's posts
- Search for other creators using same hashtags
- Deduplicate

**Path B - Audio Exploration (Reels):**
- Extract reel audio names
- Find creators using same audio
- (Limited in public API)

**Path C - Mention Graph:**
- Extract @mentions from captions
- Crawl mentioned accounts (1-hop)

**Path D - Trending-in-Category:**
- Generate embedding for user's content
- Find similar creators in vector space
- Filter by recent activity

### 2. Multi-Signal Scoring

Each candidate is scored using 6 signals:

```python
competitor_score = 
    w1 * content_similarity +      # Bio + caption similarity
    w2 * hashtag_overlap +          # Shared hashtags
    w3 * audio_overlap +            # Shared audio/music
    w4 * engagement_similarity +    # Similar engagement patterns
    w5 * tier_similarity +          # Similar follower count
    w6 * posting_time_similarity    # Similar posting times
```

**Weights are learnable** - they adapt based on user feedback.

### 3. Learning Loop

Every user action updates the system:

**When user ACCEPTS a competitor:**
- Boost weights for strong signals (score > 0.7)
- Strengthen similar candidates

**When user REJECTS a competitor:**
- Penalize weights for strong signals
- Avoid similar candidates

After just 3-5 actions, suggestions become significantly more accurate.

---

## API Endpoints

### `POST /api/competitors/discover`

Discover competitors for a user.

**Request:**
```json
{
  "instagram_handle": "mkbhd",
  "limit": 12
}
```

**Response:**
```json
[
  {
    "username": "unboxtherapy",
    "creator_id": "12345",
    "rank": 1,
    "score": 0.847,
    "signals": {
      "content_similarity": 0.82,
      "hashtag_overlap": 0.75,
      "audio_overlap": null,
      "engagement_similarity": 0.91,
      "tier_similarity": 0.88,
      "time_similarity": 0.65
    },
    "profile": {
      "full_name": "Unbox Therapy",
      "bio": "Tech reviews and unboxings",
      "follower_count": 18500000,
      "verified": true,
      "category": "Tech"
    },
    "match_reason": "Similar content themes and style"
  }
]
```

### `POST /api/competitors/{creator_id}/accept`

Accept a competitor suggestion.

**Response:**
```json
{
  "status": "success",
  "action": "accept",
  "updated_weights": {
    "content_weight": 0.22,
    "hashtag_weight": 0.24,
    "audio_weight": 0.14,
    "engagement_weight": 0.16,
    "tier_weight": 0.12,
    "time_weight": 0.12,
    "feedback_count": 1
  }
}
```

### `POST /api/competitors/{creator_id}/reject`

Reject a competitor suggestion.

### `GET /api/competitors/weights`

Get user's learned preference weights.

### `GET /api/competitors/suggestions`

Alias for `/discover` endpoint.

---

## Database Schema

### `creator_posts`
Stores post-level signals for content analysis.

**Fields:**
- `id`, `creator_id`, `platform`
- `caption`, `hashtags[]`, `mentions[]`, `audio_name`
- `post_type`, `likes`, `comments`, `views`
- `posted_at`, `posting_hour`, `posting_day`

### `competitor_candidates`
Stores generated candidates before user feedback.

**Fields:**
- `user_id`, `creator_id`, `total_score`, `rank`
- `signals_json` (signal breakdown)
- `discovery_path`, `shown_to_user`

### `user_competitor_feedback`
Tracks user accept/reject actions.

**Fields:**
- `user_id`, `creator_id`, `action`
- `confidence`, `signals_at_feedback`
- `rejection_reason` (optional)

### `user_preference_weights`
Stores learnable weights per user.

**Fields:**
- `user_id`
- `content_weight`, `hashtag_weight`, `audio_weight`
- `engagement_weight`, `tier_weight`, `time_weight`
- `feedback_count`, `last_updated_at`

---

## Usage Example

```python
from app.services.intelligence.competitor_discovery_orchestrator import CompetitorDiscoveryOrchestrator
from app.core.database import SessionLocal

db = SessionLocal()
orchestrator = CompetitorDiscoveryOrchestrator(db)

# Discover competitors
competitors = orchestrator.discover_competitors(
    user_id="user-uuid",
    username="mkbhd",
    limit=12
)

# Handle feedback
result = orchestrator.handle_feedback(
    user_id="user-uuid",
    creator_id="competitor-id",
    action="accept"
)

# Get learned weights
weights = orchestrator.get_user_weights("user-uuid")
```

---

## Testing

Run the test script:

```bash
cd backend
python test_competitor_discovery_system.py
```

This will:
1. Initialize database
2. Create test user
3. Discover competitors for @mkbhd
4. Test feedback (accept)
5. Verify weight updates

---

## Ethical Guidelines

We ONLY use:
- ✅ Public profiles
- ✅ Public posts
- ✅ Public hashtags
- ✅ Public engagement metrics

We DO NOT use:
- ❌ Login-required endpoints
- ❌ Private follower lists
- ❌ DMs or stories
- ❌ Private accounts

---

## Rate Limiting

- **Minimum delay:** 2 seconds between requests
- **Maximum delay:** 5 seconds between requests
- **Caching:** 24 hours per profile
- **Circuit breaker:** Opens after 3 consecutive failures

---

## Performance

- **Discovery time:** 30-60 seconds for new user
- **Candidates generated:** 50-200 per user
- **Top suggestions:** 12 (configurable)
- **Learning speed:** Improves after 3-5 feedback actions

---

## Future Enhancements

- [ ] Audio/reel exploration (requires Instagram API)
- [ ] Offline batch learning (nightly)
- [ ] Creator clustering
- [ ] Embedding refresh jobs
- [ ] Advanced rejection reasons

---

## License

MIT License - See LICENSE file for details.

---

**Built with ethical scraping, intelligent learning, and user trust** 🚀
