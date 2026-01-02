"""
Celery Tasks - Maintenance
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.services.intelligence.emotional_tracker import EmotionalStateTracker
from app.services.intelligence.saturation_tracker import SaturationTracker
from app.models.user import User
from app.models.user_action import EmotionalState

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.maintenance.decay_emotional_levels')
def decay_emotional_levels():
    """
    Gradually decay emotional levels for all users.
    
    Prevents levels from staying high forever.
    Runs daily at 6 AM UTC.
    """
    logger.info("Starting emotional level decay")
    
    db = next(get_db())
    
    try:
        # Get all users
        users = db.query(User).all()
        
        if not users:
            logger.warning("No users found")
            return {
                'status': 'skipped',
                'reason': 'no_users'
            }
        
        emotional_tracker = EmotionalStateTracker(db)
        
        decayed_count = 0
        
        for user in users:
            try:
                emotional_tracker.decay_emotional_levels(
                    user_id=user.id,
                    decay_rate=0.1
                )
                decayed_count += 1
                
            except Exception as e:
                logger.error(f"Failed to decay for user {user.id}: {e}")
                continue
        
        logger.info(f"Decayed emotional levels for {decayed_count} users")
        
        return {
            'status': 'success',
            'users_processed': decayed_count
        }
        
    except Exception as e:
        logger.error(f"Emotional decay failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance.reset_rapid_check_counters')
def reset_rapid_check_counters():
    """
    Reset rapid check counters for all users.
    
    Runs daily at 12:30 AM UTC.
    """
    logger.info("Resetting rapid check counters")
    
    db = next(get_db())
    
    try:
        # Reset all counters
        db.query(EmotionalState).update({'rapid_check_count': 0})
        db.commit()
        
        count = db.query(EmotionalState).count()
        
        logger.info(f"Reset rapid check counters for {count} users")
        
        return {
            'status': 'success',
            'users_processed': count
        }
        
    except Exception as e:
        logger.error(f"Counter reset failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance.cleanup_old_topics')
def cleanup_old_topics(days: int = 90):
    """
    Clean up topics not seen in X days.
    
    Runs weekly on Sunday at 3 AM UTC.
    
    Args:
        days: Number of days of inactivity before cleanup
    """
    logger.info(f"Cleaning up topics older than {days} days")
    
    db = next(get_db())
    
    try:
        saturation_tracker = SaturationTracker(db)
        deleted_count = saturation_tracker.cleanup_old_topics(days=days)
        
        logger.info(f"Cleaned up {deleted_count} old topics")
        
        return {
            'status': 'success',
            'topics_deleted': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Topic cleanup failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.maintenance.rebuild_vector_store')
def rebuild_vector_store():
    """
    Rebuild vector store index (removes deleted entries).
    
    Should be run manually or scheduled weekly.
    """
    logger.info("Rebuilding vector store index")
    
    try:
        from app.services.intelligence.vector_store import get_vector_store
        
        vector_store = get_vector_store()
        
        # Note: Current vector store doesn't support rebuild
        # This would need to be implemented
        logger.warning("Vector store rebuild not yet implemented")
        
        return {
            'status': 'skipped',
            'reason': 'not_implemented'
        }
        
    except Exception as e:
        logger.error(f"Vector store rebuild failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
