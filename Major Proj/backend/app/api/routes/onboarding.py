"""
Onboarding API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.services.decision_assistant import DecisionAssistant
from app.api.deps import get_current_user
from app.models.user import User
from app.models.dynamic_niche import DynamicNiche
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ProfileData(BaseModel):
    user_id: str
    platform: Optional[str] = "instagram"
    bio: Optional[str] = None
    follower_count: Optional[int] = 0
    content_samples: Optional[List[str]] = []

class OnboardingResponse(BaseModel):
    user_id: str
    niche: Optional[Dict[str, Any]]
    competitors: List[Dict[str, Any]]
    onboarded_at: str

@router.post("/analyze", response_model=OnboardingResponse)
async def analyze_profile(
    profile: ProfileData,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Disabled for testing
):
    """
    Onboard a creator by analyzing their profile.
    
    1. Generates embedding from bio + content
    2. Discovers dynamic niche
    3. Identifies competitors
    4. Initializes behavioral learning
    5. ✅ NEW: Stores dynamic niche in database
    """
    try:
        assistant = DecisionAssistant(db)
        
        # ✅ STEP 1: Get onboarding result with niche discovery
        result = await assistant.onboard_creator(
            user_id=profile.user_id,
            profile_data=profile.dict(),
            content_samples=profile.content_samples
        )
        
        # ✅ STEP 2: Store dynamic niche in database
        if result.get('niche'):
            niche_data = result['niche']
            
            # Check if niche already exists
            dynamic_niche = db.query(DynamicNiche).filter_by(
                id=niche_data['niche_id']
            ).first()
            
            if not dynamic_niche:
                # Create new niche
                dynamic_niche = DynamicNiche(
                    id=niche_data['niche_id'],
                    name=niche_data['label'],
                    embedding_centroid=niche_data['centroid'],
                    member_count=0,
                    is_micro=niche_data.get('is_micro', False),
                    descriptors=niche_data.get('descriptors', [])
                )
                db.add(dynamic_niche)
                logger.info(f"✅ Created new niche: {dynamic_niche.name}")
            
            # ✅ STEP 3: Update member count
            dynamic_niche.member_count = db.query(User).filter(
                User.niche_id == niche_data['niche_id']
            ).count() + 1
            
            # ✅ STEP 4: Link user to niche
            user = db.query(User).filter_by(id=profile.user_id).first()
            if user:
                user.niche_id = niche_data['niche_id']
                logger.info(
                    f"✅ Linked user {profile.user_id} to niche {dynamic_niche.name} "
                    f"(member #{dynamic_niche.member_count})"
                )
            else:
                logger.warning(f"User {profile.user_id} not found in database")
            
            db.commit()
            logger.info("✅ Dynamic niche storage complete")
        else:
            logger.warning(f"No niche discovered for user {profile.user_id}")
        
        return result
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Onboarding failed for {profile.user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
