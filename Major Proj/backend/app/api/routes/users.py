"""
User management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.niche import Niche
from app.api.schemas import UserResponse, UserUpdate, NicheResponse
from app.api.routes.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    
    # Update fields if provided
    if user_update.selected_niches is not None:
        current_user.selected_niches = user_update.selected_niches
    
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    
    if user_update.notification_time is not None:
        current_user.notification_time = user_update.notification_time
    
    if user_update.preferences is not None:
        current_user.preferences = user_update.preferences
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User profile updated: {current_user.email}")
    
    return current_user


@router.get("/niches", response_model=List[NicheResponse])
async def get_available_niches(db: Session = Depends(get_db)):
    """Get list of available niches"""
    niches = db.query(Niche).all()
    return niches


@router.post("/niches/{niche_id}/select")
async def select_niche(
    niche_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a niche to user's selected niches"""
    
    # Verify niche exists
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Niche not found"
        )
    
    # Add to selected niches if not already there
    if niche.name not in current_user.selected_niches:
        current_user.selected_niches.append(niche.name)
        db.commit()
        logger.info(f"User {current_user.email} selected niche: {niche.name}")
    
    return {"message": f"Niche '{niche.name}' added to your selection"}


@router.delete("/niches/{niche_id}/unselect")
async def unselect_niche(
    niche_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a niche from user's selected niches"""
    
    niche = db.query(Niche).filter(Niche.id == niche_id).first()
    if not niche:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Niche not found"
        )
    
    # Remove from selected niches
    if niche.name in current_user.selected_niches:
        current_user.selected_niches.remove(niche.name)
        db.commit()
        logger.info(f"User {current_user.email} unselected niche: {niche.name}")
    
    return {"message": f"Niche '{niche.name}' removed from your selection"}
