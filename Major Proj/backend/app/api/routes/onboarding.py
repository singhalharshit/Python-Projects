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
    username: str  # ✅ Instagram username
    user_id: str  # ✅ User's unique ID (for tracking)
    platform: Optional[str] = "instagram"
    bio: Optional[str] = None
    recent_captions: Optional[List[str]] = []  # ✅ NEW: 5-10 recent captions
    hashtags: Optional[List[str]] = []  # ✅ NEW: User's hashtags
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
    use_real_instagram: bool = True,  # ✅ NEW: Toggle for real Instagram
    # current_user: User = Depends(get_current_user) # Disabled for testing
):
    """
    Onboard a creator by analyzing their profile.
    
    1. Generates embedding from bio + content
    2. Discovers dynamic niche
    3. ✅ NEW: Identifies competitors from REAL Instagram (if enabled)
    4. Initializes behavioral learning
    5. Stores dynamic niche in database
    """
    try:
        logger.info(f"Onboarding {profile.user_id} (real_instagram={use_real_instagram})...")
        
        assistant = DecisionAssistant(db)
        
        competitors = []
        discovery_mode = "semantic_discovery"  # Use semantic discovery
        
        # ✅ SIMPLE WORKING Discovery
        if use_real_instagram and profile.platform == 'instagram':
            logger.info("✅ Using SIMPLE working competitor discovery...")
            
            from app.services.simple_competitor_discovery import get_simple_discovery
            from app.services.intelligence.embedding_service import EmbeddingService
            
            embedding_service = EmbeddingService()
            simple_discovery = get_simple_discovery(embedding_service)
            
            # Discover competitors
            competitors = simple_discovery.discover_competitors(
                username=profile.username,
                bio=profile.bio or "",
                hashtags=profile.hashtags or [],
                recent_captions=profile.recent_captions or [],
                limit=20
            )
            
            logger.info(f"✅ Found {len(competitors)} competitors")
            
            # ✅ NEW: Store discovered competitors for learning
            if competitors:
                from app.services.competitor_learning_system import get_learning_system
                learning_system = get_learning_system(db)
                
                # Infer niche from profile
                inferred_niche = profile.bio or "general"
                
                try:
                    learning_system.store_discovered_competitors(
                        competitors=competitors,
                        source_username=profile.username,
                        niche=inferred_niche
                    )
                    logger.info("✅ Stored competitors for future learning")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store competitors: {e}")

        # Compose onboarding result
        result = {
            'user_id': profile.user_id,
            'niche': None,  # Will be set below
            'competitors': competitors,
            'discovery_mode': discovery_mode,
            'onboarded_at': __import__('datetime').datetime.utcnow().isoformat()
        }

        # OPTION B: Use vector similarity (fallback)
        if not competitors:
            logger.info("⚠️  Using vector similarity (fallback)...")
            
            result = await assistant.onboard_creator(
                user_id=profile.user_id,
                profile_data=profile.dict(),
                content_samples=profile.content_samples
            )
        
        # ✅ STEP 2: Discover and store dynamic niche
        if not result.get('niche'):
            # Discover niche from profile
            from app.services.intelligence.niche_discovery import get_niche_discovery
            from app.services.signals.abstract_signal import CreatorEmbedding
            from app.services.intelligence.embedding_service import EmbeddingService
            import numpy as np
            
            embedding_service = EmbeddingService()
            niche_discovery = get_niche_discovery(db)
            
            # Create embedding
            bio_text = f"{profile.bio or ''} {profile.platform}"
            theme_embedding = embedding_service.encode_text(bio_text)
            
            creator_embedding = CreatorEmbedding(
                theme=theme_embedding,
                tone=np.zeros(5),
                format=np.zeros(4),
                trajectory=np.zeros(4),
                creator_id=profile.user_id,
                platform=profile.platform,
                analyzed_at=__import__('datetime').datetime.utcnow(),
                post_count=0
            )
            
            # Discover niche
            niche = niche_discovery.discover_niche_for_creator(creator_embedding)
            
            if niche:
                result['niche'] = niche.to_dict()
        
        # ✅ STEP 3: Store dynamic niche in database
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
                    is_micro=niche_data.get('is_micro', 0),
                    descriptors=niche_data.get('descriptors', [])
                )
                db.add(dynamic_niche)
                logger.info(f"✅ Created new niche: {dynamic_niche.name}")
            
            # ✅ STEP 4: Update member count
            dynamic_niche.member_count = db.query(User).filter(
                User.niche_id == niche_data['niche_id']
            ).count() + 1
            
            # ✅ STEP 5: Link user to niche
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
