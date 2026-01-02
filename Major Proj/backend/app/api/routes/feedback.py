"""
Feedback API - Track user actions for self-learning

This is how the system learns without asking questions.
"""

import logging
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.intelligence.feedback_loop import FeedbackLoop
from app.services.intelligence.preference_learner import PreferenceLearner
from app.services.intelligence.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


class ActionFeedback(BaseModel):
    """User action on a recommendation"""
    action: Literal["viewed", "accepted", "rejected", "followed", "ignored"]
    time_spent_seconds: int = 0  # How long user viewed the recommendation
    context: dict = {}  # Additional context (optional)


class FeedbackResponse(BaseModel):
    """Response after processing feedback"""
    status: str
    message: str
    learning_applied: bool
    preference_updated: bool


@router.post(
    "/recommendations/{recommendation_id}/feedback",
    response_model=FeedbackResponse,
    summary="Track user action on recommendation",
    description="""
    Track how user responded to a recommendation. This is the core learning mechanism.
    
    Actions:
    - **viewed**: User saw the recommendation (neutral signal)
    - **accepted**: User agrees with the recommendation (weak positive)
    - **rejected**: User disagrees with the recommendation (negative signal)  
    - **followed**: User actually posted about it (STRONG positive)
    - **ignored**: User didn't interact (weak negative)
    
    The system learns from these actions WITHOUT asking questions.
    """
)
async def track_recommendation_feedback(
    recommendation_id: str,
    feedback: ActionFeedback,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process user action and update preference learning.
    """
    
    logger.info(
        f"Feedback received: user={current_user.id}, "
        f"rec={recommendation_id}, action={feedback.action}"
    )
    
    try:
        # Initialize feedback loop
        embedding_service = EmbeddingService()
        preference_learner = PreferenceLearner(db, embedding_service)
        feedback_loop = FeedbackLoop(db, preference_learner, embedding_service)
        
        # Process the action
        await feedback_loop.process_user_action(
            user_id=current_user.id,
            recommendation_id=recommendation_id,
            action=feedback.action,
            timestamp=datetime.utcnow(),
            context={
                "time_spent": feedback.time_spent_seconds,
                **feedback.context
            }
        )
        
        # Return success
        return FeedbackResponse(
            status="success",
            message=f"Action '{feedback.action}' recorded and learning applied",
            learning_applied=True,
            preference_updated=feedback.action in ["accepted", "rejected", "followed"]
        )
        
    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feedback: {str(e)}"
        )


@router.get(
    "/users/me/learning-insights",
    summary="Get learning insights",
    description="See how the system has learned your preferences"
)
async def get_learning_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get insights into what the system has learned about user.
    
    This provides transparency into the learning process.
    """
    
    try:
        embedding_service = EmbeddingService()
        preference_learner = PreferenceLearner(db, embedding_service)
        feedback_loop = FeedbackLoop(db, preference_learner, embedding_service)
        
        # Get pattern analysis
        pattern_analysis = await feedback_loop.analyze_pattern_changes(
            user_id=current_user.id,
            lookback_days=30
        )
        
        # Get behavioral patterns
        time_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id=current_user.id,
            pattern_type="time"
        )
        
        content_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id=current_user.id,
            pattern_type="content"
        )
        
        mood_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id=current_user.id,
            pattern_type="mood"
        )
        
        return {
            "user_id": current_user.id,
            "learning_status": "active",
            "patterns": {
                "preference_drift": pattern_analysis,
                "time_preferences": time_pattern,
                "content_preferences": content_pattern,
                "decision_mood": mood_pattern
            },
            "transparency_note": (
                "These insights show what the system has learned about your "
                "preferences through your actions. We never sell or share this data."
            )
        }
        
    except Exception as e:
        logger.error(f"Error getting learning insights: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve insights: {str(e)}"
        )


@router.post(
    "/users/me/reset-learning",
    summary="Reset learning preferences",
    description="Clear learned preferences and start fresh"
)
async def reset_learning_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allow user to reset their learned preferences.
    
    Privacy and control are important.
    """
    
    logger.info(f"Resetting preferences for user {current_user.id}")
    
    try:
        embedding_service = EmbeddingService()
        preference_learner = PreferenceLearner(db, embedding_service)
        
        # Reset preference vector
        preference_learner.reset_preferences(current_user.id)
        
        return {
            "status": "success",
            "message": "Preference learning has been reset. The system will learn fresh from your future actions.",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resetting preferences: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset preferences: {str(e)}"
        )
