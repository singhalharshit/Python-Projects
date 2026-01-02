"""
Celery Application Configuration
"""
from celery import Celery
from celery.schedules import crontab
import os

# Get Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery app
celery_app = Celery(
    'decision_assistant',
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Celery Beat schedule (periodic tasks)
celery_app.conf.beat_schedule = {
    # Collect trends every 2 hours
    'collect-trends-every-2-hours': {
        'task': 'app.tasks.trend_collection.collect_trends_for_all_niches',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
    
    # Generate daily recommendations at midnight UTC
    'generate-daily-recommendations': {
        'task': 'app.tasks.recommendation_generation.generate_daily_recommendations',
        'schedule': crontab(hour=0, minute=0),  # Midnight UTC
    },
    
    # Decay emotional levels daily at 6 AM UTC
    'decay-emotional-levels': {
        'task': 'app.tasks.maintenance.decay_emotional_levels',
        'schedule': crontab(hour=6, minute=0),  # 6 AM UTC
    },
    
    # Reset rapid check counters daily
    'reset-rapid-check-counters': {
        'task': 'app.tasks.maintenance.reset_rapid_check_counters',
        'schedule': crontab(hour=0, minute=30),  # 12:30 AM UTC
    },
    
    # Clean up old topics weekly
    'cleanup-old-topics': {
        'task': 'app.tasks.maintenance.cleanup_old_topics',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday 3 AM
    },
}

# Import tasks (this registers them with Celery)
from app.tasks import trend_collection, recommendation_generation, maintenance
