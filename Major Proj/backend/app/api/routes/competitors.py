"""
Competitor Discovery API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.services.decision_assistant import DecisionAssistant

router = APIRouter()

class CompetitorResponse(BaseModel):
    user_id: str
    relevance: float
    differentiation: float
    aspirational_distance: float
    total_score: float
    metadata: Dict[str, Any]

@router.get("/discover/{user_id}", response_model=List[CompetitorResponse])
async def discover_competitors(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Dynamically discover new competitors for a user.
    Uses vector similarity + diversity filtering.
    """
    try:
        assistant = DecisionAssistant(db)
        
        # We need to access internal component for now as orchestrator wraps it
        # Ideally orchestrator should expose this method
        # But for now we can get the creator embedding and call discovery directly
        # Or better, let's just use what we have available via private methods or extend orchestrator
        
        # Let's assume we extend DecisionAssistant or use its internal components
        vector_store = assistant.vector_store
        comp_engine = assistant.competitor_discovery
        
        creator_data = vector_store.get_creator_embedding(user_id)
        if not creator_data:
            raise HTTPException(status_code=404, detail="Creator not found")
            
        # Reconstruct embedding object (simplified)
        from app.services.signals.abstract_signal import CreatorEmbedding
        import numpy as np
        from datetime import datetime
        
        embedding = CreatorEmbedding(
            theme=creator_data,
            tone=np.zeros(5),
            format=np.zeros(4),
            trajectory=np.zeros(4),
            creator_id=user_id,
            platform='unknown',
            analyzed_at=datetime.utcnow(),
            post_count=0
        )
        
        competitors = comp_engine.discover_competitors(
            creator_embedding=embedding,
            k=20
        )
        
        return [c.to_dict() for c in competitors]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
