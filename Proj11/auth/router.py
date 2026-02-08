from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth.schemas import LoginRequest, TokenResponse
from auth.service import authenticate_user
from core.security import create_access_token
from db.session import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {"sub": user.username, "role": user.role}
    )
    return {"access_token": token}
