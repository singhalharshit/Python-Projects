from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.intelligence.profile_analyzer_v2 import profile_analyzer

from app.services.user_preferences import user_preferences_service
from app.services.intelligence.vector_store import vector_store
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class AnalyzeRequest(BaseModel):
    username: str
    user_id: Optional[str] = None  # For personalization

class CompetitorSuggestion(BaseModel):
    id: str
    name: str
    handle: str
    avatar: str
    subs: str
    tags: List[str]
    content_style: str
    avg_views: str
    confidence_score: Optional[float] = None
    match_reason: Optional[str] = None

class AnalysisResponse(BaseModel):
    username: str
    inferred_niche: str
    suggested_competitors: List[CompetitorSuggestion]

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_profile(request: AnalyzeRequest):
    """
    Analyze an Instagram profile to suggest niche and competitors.
    Supports personalization via user_id.
    """
    try:
        result = profile_analyzer.analyze_profile(
            request.username, 
            user_id=request.user_id
        )
        logger.info(f"Profile analysis for {request.username}: {len(result['suggested_competitors'])} suggestions")
        return result
    except Exception as e:
        logger.error(f"Error analyzing profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SimilarRequest(BaseModel):
    selected_ids: List[str]
    user_id: Optional[str] = None  # For personalization

@router.post("/similar", response_model=List[CompetitorSuggestion])
async def get_similar_creators(request: SimilarRequest):
    """
    Suggest more creators like those already selected.
    Uses advanced similarity matching and personalization.
    """
    try:
        result = profile_analyzer.get_similar_creators(
            request.selected_ids,
            user_id=request.user_id
        )
        logger.info(f"Similar creators for {len(request.selected_ids)} selections: {len(result)} suggestions")
        return result
    except Exception as e:
        logger.error(f"Error fetching similar creators: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class FeedbackRequest(BaseModel):
    user_id: str
    creator_id: str
    action: str  # "selected" or "rejected"
    creator_tags: List[str]
    reason: Optional[str] = None


@router.post("/feedback")
async def track_feedback(request: FeedbackRequest):
    """
    Track user feedback (selections/rejections) to improve recommendations.
    Uses vector math to update user embedding.
    """
    try:
        # Get creator embedding from vector store
        creator_embedding = vector_store.get_creator_embedding(request.creator_id)
        
        if creator_embedding is None:
            raise HTTPException(status_code=404, detail=f"Creator {request.creator_id} not found")
        
        if request.action == "selected":
            user_preferences_service.track_selection(
                request.user_id,
                request.creator_id,
                creator_embedding,
                request.creator_tags
            )
        elif request.action == "rejected":
            user_preferences_service.track_rejection(
                request.user_id,
                request.creator_id,
                creator_embedding,
                request.creator_tags,
                request.reason
            )
        else:
            raise HTTPException(status_code=400, detail="Action must be 'selected' or 'rejected'")
        
        logger.info(f"ML Feedback tracked: {request.action} for creator {request.creator_id} by user {request.user_id}")
        
        return {
            "status": "success",
            "message": f"ML-based feedback recorded: {request.action}",
            "ml_powered": True
        }
    except Exception as e:
        logger.error(f"Error tracking feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """
    Get user preference statistics and insights.
    """
    try:
        stats = user_preferences_service.get_user_stats(user_id)
        return stats
    except Exception as e:
        logger.error(f"Error fetching user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))
