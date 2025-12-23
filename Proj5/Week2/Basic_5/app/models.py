#models.py

from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None