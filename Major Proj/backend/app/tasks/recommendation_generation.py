"""
Celery Tasks - Daily Recommendation Generation
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.core.database import get_db
from app.services.decision_assistant import DecisionAssistant
from app.models.user import User
from app.models.recommendation import Recommendation

logger = logging.getLogger(__name__)


@celery_app.task(name='app.tasks.recommendation_generation.generate_daily_recommendations')
def generate_daily_recommendations():
    """
    Generate daily recommendations for all active users.
    
    Runs daily at midnight UTC via Celery Beat.
    """
    logger.info("Starting daily recommendation generation")
    
    db = next(get_db())
    
    try:
        # Get all active users
        users = db.query(User).filter_by(is_active=True).all()
        
        if not users:
            logger.warning("No active users found")
            return {
                'status': 'skipped',
                'reason': 'no_users',
                'users_processed': 0
            }
        
        logger.info(f"Generating recommendations for {len(users)} users")
        
        # Initialize decision assistant
        decision_assistant = DecisionAssistant(db)
        
        results = []
        
        for user in users:
            try:
                # Generate decision
                decision = await decision_assistant.get_daily_decision(user.id)
                
                # Store in database
                recommendation = Recommendation(
                    id=f"rec_{user.id}_{datetime.utcnow().timestamp()}",
                    user_id=user.id,
                    action=decision.action,
                    topic=decision.topic,
                    confidence=decision.confidence,
                    explanation=decision.explanation,
                    timing=decision.timing,
                    alternatives=decision.alternatives,
                    avoid_list=decision.avoid,
                    emotional_context=decision.emotional_context,
                    metadata_json=decision.metadata,
                    generated_at=decision.generated_at,
                    created_at=datetime.utcnow()
                )
                
                db.add(recommendation)
                db.commit()
                
                results.append({
                    'user_id': user.id,
                    'action': decision.action,
                    'topic': decision.topic,
                    'confidence': decision.confidence
                })
                
                logger.info(
                    f"Generated recommendation for {user.id}: "
                    f"{decision.action} - {decision.topic}"
                )
                
            except Exception as e:
                logger.error(f"Failed to generate for user {user.id}: {e}")
                continue
        
        logger.info(f"Recommendation generation complete: {len(results)} users processed")
        
        return {
            'status': 'success',
            'users_processed': len(results),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()


@celery_app.task(name='app.tasks.recommendation_generation.generate_recommendation_for_user')
def generate_recommendation_for_user(user_id: str):
    """
    Generate recommendation for a specific user (on-demand).
    
    Args:
        user_id: User ID
    """
    logger.info(f"Generating recommendation for user {user_id}")
    
    db = next(get_db())
    
    try:
        # Initialize decision assistant
        decision_assistant = DecisionAssistant(db)
        
        # Generate decision
        decision = await decision_assistant.get_daily_decision(user_id)
        
        # Store in database
        recommendation = Recommendation(
            id=f"rec_{user_id}_{datetime.utcnow().timestamp()}",
            user_id=user_id,
            action=decision.action,
            topic=decision.topic,
            confidence=decision.confidence,
            explanation=decision.explanation,
            timing=decision.timing,
            alternatives=decision.alternatives,
            avoid_list=decision.avoid,
            emotional_context=decision.emotional_context,
            metadata_json=decision.metadata,
            generated_at=decision.generated_at,
            created_at=datetime.utcnow()
        )
        
        db.add(recommendation)
        db.commit()
        
        logger.info(f"Generated recommendation for {user_id}: {decision.action}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'recommendation_id': recommendation.id,
            'action': decision.action,
            'topic': decision.topic
        }
        
    except Exception as e:
        logger.error(f"Failed to generate for user {user_id}: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }
    
    finally:
        db.close()
