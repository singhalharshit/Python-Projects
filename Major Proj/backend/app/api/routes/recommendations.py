from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import logging
from pydantic import BaseModel

from app.core.database import get_db
from app.services.recommendation_engine import RecommendationEngine
from app.api.schemas import RecommendationGenerated, RecommendationResponse
from app.models.recommendation import Recommendation
from app.models.niche import Niche

router = APIRouter()
logger = logging.getLogger(__name__)

# Temporary keyword mapping for MVP
NICHE_KEYWORDS = {
    "tech_creators": ["AI", "coding", "python", "developer", "tech news"],
    "gaming_creators": ["gaming", "esports", "new releases", "gameplay", "streamer"],
    "business_creators": ["startup", "entrepreneurship", "productivity", "marketing"],
    "lifestyle_creators": ["wellness", "productivity", "vlog", "lifestyle"]
}

class GenerateRequest(BaseModel):
    niche: str
    keywords: List[str] = []

@router.post("/generate", response_model=RecommendationGenerated)
async def generate_recommendation_manual(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Manually trigger recommendation generation for testing.
    This runs the engine in real-time (can take 5-10 seconds).
    """
    try:
        engine = RecommendationEngine(db)
        
        # Use provided keywords or defaults
        keywords = request.keywords
        if not keywords:
            keywords = NICHE_KEYWORDS.get(request.niche, ["general"])
            
        logger.info(f"Generating recommendation for {request.niche} with keywords: {keywords}")
        
        result = engine.generate_recommendation(
            niche=request.niche,
            keywords=keywords
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily/{niche_name}", response_model=RecommendationGenerated)
async def get_daily_recommendation(
    niche_name: str,
    db: Session = Depends(get_db)
):
    """
    Get the daily recommendation for a specific niche.
    For MVP, this generates it on-the-fly if not cached (caching to be added).
    """
    # 1. Check if we already have a recommendation for today (TODO: Implement DB check)
    # For now, always generate fresh
    
    try:
        # Resolve keywords
        keywords = NICHE_KEYWORDS.get(niche_name)
        if not keywords:
            # Fallback for unknown niches
            keywords = [niche_name, "news", "trends"]
            
        engine = RecommendationEngine(db)
        
        result = engine.generate_recommendation(
            niche=niche_name,
            keywords=keywords
        )
        
        # TODO: Save to database (asynchronously)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting daily recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
