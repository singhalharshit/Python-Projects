"""
User Actions API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import numpy as np

from app.core.database import get_db
from app.services.decision_assistant import DecisionAssistant
from app.services.intelligence.feedback_loop import FeedbackLoop
from app.services.intelligence.preference_learner import PreferenceLearner
from app.services.intelligence.embedding_service import EmbeddingService
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class UserActionRequest(BaseModel):
    user_id: str
    action_type: str  # viewed, accepted, rejected, followed, ignored
    content_vector: Optional[List[float]] = None
    recommendation_id: Optional[str] = None
    time_spent: Optional[int] = None  # seconds
    context: Optional[Dict[str, Any]] = {}

@router.post("/record")
async def record_action(
    action: UserActionRequest,
    db: Session = Depends(get_db)
):
    """
    ✅ ENHANCED: Record a user action with full feedback loop integration.
    This is the CORE of the self-learning mechanism.
    
    Actions:
    - viewed: User saw the recommendation (neutral)
    - accepted: User agreed with recommendation (weak positive)
    - followed: User actually posted about it (STRONG positive)
    - rejected: User disagreed (negative)
    - ignored: User didn't interact (weak negative)
    """
    try:
        # ✅ STEP 1: Validate action type
        valid_actions = ['viewed', 'accepted', 'rejected', 'followed', 'ignored']
        if action.action_type not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action type. Must be one of: {valid_actions}"
            )
        
        # ✅ STEP 2: Initialize full feedback loop
        feedback_loop = FeedbackLoop(
            db=db,
            preference_learner=PreferenceLearner(db),
            embedding_service=EmbeddingService()
        )
        
        # ✅ STEP 3: Build context
        full_context = action.context or {}
        if action.time_spent is not None:
            full_context['time_spent'] = action.time_spent
        full_context['timestamp'] = datetime.utcnow().isoformat()
        full_context['platform'] = full_context.get('platform', 'web')
        
        # ✅ STEP 4: Process action through feedback loop
        if action.recommendation_id:
            await feedback_loop.process_user_action(
                user_id=action.user_id,
                recommendation_id=action.recommendation_id,
                action=action.action_type,
                timestamp=datetime.utcnow(),
                context=full_context
            )
            
            logger.info(
                f"✅ Processed {action.action_type} for user {action.user_id} "
                f"on recommendation {action.recommendation_id}"
            )
        else:
            # Fallback to basic action recording
            assistant = DecisionAssistant(db)
            vector = np.array(action.content_vector) if action.content_vector else None
            
            await assistant.record_action(
                user_id=action.user_id,
                action_type=action.action_type,
                content_vector=vector,
                context=full_context
            )
            
            logger.info(f"✅ Recorded {action.action_type} for user {action.user_id}")
        
        # ✅ STEP 5: Analyze if preferences are changing (optional insight)
        pattern_change = await feedback_loop.analyze_pattern_changes(
            user_id=action.user_id,
            lookback_days=30
        )
        
        # ✅ STEP 6: Return learning insights
        return {
            "status": "processed",
            "action": action.action_type,
            "learning_status": {
                "interpretation": pattern_change.get('interpretation', 'stable'),
                "acceptance_rate": pattern_change.get('late_acceptance_rate', 0.0),
                "drift": pattern_change.get('drift', 0.0),
                "action_count": pattern_change.get('action_count', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning-insights/{user_id}")
async def get_learning_insights(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    ✅ NEW: Get detailed learning insights for a user.
    
    Returns patterns the system has detected:
    - Time preferences (when user typically engages)
    - Content preferences (what topics user accepts)
    - Mood/risk tolerance (adventurous vs conservative)
    - Preference stability (how consistent are choices)
    """
    try:
        # ✅ Initialize feedback loop
        feedback_loop = FeedbackLoop(
            db=db,
            preference_learner=PreferenceLearner(db),
            embedding_service=EmbeddingService()
        )
        
        # ✅ Detect behavioral patterns
        time_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id, 'time'
        )
        content_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id, 'content'
        )
        mood_pattern = await feedback_loop.detect_behavioral_patterns(
            user_id, 'mood'
        )
        
        # ✅ Get preference stability
        pattern_analysis = await feedback_loop.analyze_pattern_changes(
            user_id, 30
        )
        
        logger.info(f"✅ Retrieved learning insights for {user_id}")
        
        return {
            "user_id": user_id,
            "time_pattern": time_pattern,
            "content_pattern": content_pattern,
            "mood_pattern": mood_pattern,
            "preference_stability": {
                "interpretation": pattern_analysis.get('interpretation'),
                "acceptance_rate": pattern_analysis.get('late_acceptance_rate', 0.0),
                "drift": pattern_analysis.get('drift', 0.0),
                "action_count": pattern_analysis.get('action_count', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get insights for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
