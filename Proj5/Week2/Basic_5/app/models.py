from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    username: str
    email: EmailStr


class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: str
