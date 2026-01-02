"""
Daily Decision API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.decision_assistant import DecisionAssistant
from app.core.cache import get_cache_service

router = APIRouter()

class DailyDecisionResponse(BaseModel):
    action: str
    topic: str
    confidence: float
    explanation: str
    timing: float
    alternatives: List[Dict[str, Any]]
    avoid_list: List[Dict[str, Any]]
    emotional_context: Dict[str, Any]
    generated_at: str

@router.get("/daily/{user_id}", response_model=DailyDecisionResponse)
async def get_daily_decision(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the ONE calm daily decision for a user.
    Checks Redis cache first, then generates if needed.
    """
    try:
        # Check cache
        cache = get_cache_service()
        cached = cache.get_cached_recommendation(user_id)
        if cached:
            return cached
        
        # Generate new
        assistant = DecisionAssistant(db)
        decision = await assistant.get_daily_decision(user_id)
        
        # Convert to dict
        result = decision.to_dict()
        
        # Cache it
        cache.cache_recommendation(user_id, result)
        
        return result
        
    except ValueError as e:
        # User not found/onboarded
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
