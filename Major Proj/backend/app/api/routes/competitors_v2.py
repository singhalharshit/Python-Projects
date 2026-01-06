"""
Competitor Discovery API Routes (New Implementation)
Uses Creator Similarity Engine with ethical scraping and learning loop
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.user import User
from app.services.intelligence.competitor_discovery_orchestrator import CompetitorDiscoveryOrchestrator

router = APIRouter()


# Request/Response Models
class DiscoverRequest(BaseModel):
    """Request to discover competitors"""
    instagram_handle: str
    limit: Optional[int] = 12


class FeedbackRequest(BaseModel):
    """Request to provide feedback on a competitor"""
    creator_id: str
    action: str  # 'accept' or 'reject'


class CompetitorResponse(BaseModel):
    """Competitor suggestion response"""
    username: str
    creator_id: Optional[str]
    rank: int
    score: float
    signals: Dict[str, Optional[float]]
    profile: Dict[str, Any]
    match_reason: str


@router.post("/discover", response_model=List[CompetitorResponse])
async def discover_competitors(
    request: DiscoverRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover competitors for a user.
    
    This endpoint:
    1. Generates 50-200 candidates via multiple paths
    2. Scores them using multi-signal weighted formula
    3. Returns top N suggestions
    
    The system learns from your feedback to improve suggestions over time.
    """
    try:
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        competitors = orchestrator.discover_competitors(
            user_id=str(current_user.id),
            username=request.instagram_handle,
            limit=request.limit
        )
        
        # Check if it's a low confidence or error response
        if competitors and isinstance(competitors[0], dict) and 'message' in competitors[0]:
            # Return empty list with message in headers or raise exception
            raise HTTPException(
                status_code=200,
                detail=competitors[0].get('message', 'No suggestions available')
            )
        
        return competitors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{creator_id}/accept")
async def accept_competitor(
    creator_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept a competitor suggestion.
    
    This updates your preference weights to favor similar competitors.
    """
    try:
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        result = orchestrator.handle_feedback(
            user_id=str(current_user.id),
            creator_id=creator_id,
            action='accept'
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{creator_id}/reject")
async def reject_competitor(
    creator_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a competitor suggestion.
    
    This updates your preference weights to avoid similar competitors.
    """
    try:
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        result = orchestrator.handle_feedback(
            user_id=str(current_user.id),
            creator_id=creator_id,
            action='reject'
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weights")
async def get_user_weights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's learned preference weights.
    
    These weights show which signals the system prioritizes for you.
    """
    try:
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        weights = orchestrator.get_user_weights(str(current_user.id))
        
        return weights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_suggestions(
    instagram_handle: str,
    limit: int = 12,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized competitor suggestions.
    
    Alias for /discover endpoint.
    """
    try:
        orchestrator = CompetitorDiscoveryOrchestrator(db)
        
        competitors = orchestrator.discover_competitors(
            user_id=str(current_user.id),
            username=instagram_handle,
            limit=limit
        )
        
        return competitors
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
