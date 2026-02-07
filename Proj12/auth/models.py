# auth/models

from pydantic import BaseModel
from datetime import datetime

class UserSignUp(BaseModel):
    username: str
    password: str
    role: str = "User"


class UserReturn(BaseModel):
    username: str
    role: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
