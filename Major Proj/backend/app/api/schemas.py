"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# ===== Auth Schemas =====

class UserSignup(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    selected_niches: List[str] = Field(default=[], description="List of niche IDs")
    timezone: str = Field(default="UTC")


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


# ===== User Schemas =====

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    selected_niches: List[str] = []
    timezone: str = "UTC"
    notification_time: str = "09:00"


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User update request"""
    selected_niches: Optional[List[str]] = None
    timezone: Optional[str] = None
    notification_time: Optional[str] = None
    preferences: Optional[dict] = None


# ===== Niche Schemas =====

class NicheResponse(BaseModel):
    """Niche response schema"""
    id: UUID
    name: str
    description: Optional[str]
    current_vibe: Optional[str]
    vibe_description: Optional[str]
    
    class Config:
        from_attributes = True


# ===== Recommendation Schemas =====

class AntiTrend(BaseModel):
    """Anti-trend (saturated topic) schema"""
    topic: str
    reason: str
    advice: str


class Vibe(BaseModel):
    """Niche vibe schema"""
    current_mood: str
    description: str
    confidence: str


class Timing(BaseModel):
    """Posting timing suggestion"""
    best_time: datetime
    reason: str


class RecommendationResponse(BaseModel):
    """Daily recommendation response"""
    id: UUID
    date: str
    niche: str
    action: str
    topic: Optional[str]
    reasoning: str
    confidence_score: int
    certainty_level: str
    signal_health: dict
    anti_trends: List[AntiTrend]
    vibe: Vibe
    timing: Optional[Timing]
    created_at: datetime
    
    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    """User feedback on recommendation"""
    recommendation_id: UUID
    feedback: str = Field(..., description="'accepted', 'ignored', or 'modified'")
    outcome: Optional[dict] = Field(default=None, description="Optional outcome data")


# ===== Signal Health Schemas =====

class SignalHealthResponse(BaseModel):
    """Signal health status response"""
    source: str
    status: str
    success_rate: float
    last_success: Optional[datetime]
    response_time_ms: Optional[int]
    
    class Config:
        from_attributes = True
