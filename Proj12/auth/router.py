# auth/router

from fastapi import APIRouter,Depends,HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth.models import UserLogin,UserReturn,UserSignUp,TokenResponse
from db.session import get_db
from db.models import User
from core.security import hash_password,create_access_token
from core.dependencies import get_current_user
from datetime import datetime
from auth.service import authenticate_user


router = APIRouter(prefix="/user")

@router.post("/sign_up", response_model=UserReturn)
def user_signup(data: UserSignUp, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=data.username,
        password=hash_password(data.password),
        role=data.role,
        created_on=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.post("/login",response_model=TokenResponse)
def user_login(form_data: OAuth2PasswordRequestForm = Depends(),db:Session = Depends(get_db)):
    user = authenticate_user(form_data.username,form_data.password,db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token= create_access_token(
        {
            "sub":user.username,
            "role": user.role
        }
    )
    return {
    "access_token": token
    }


@router.get("/check_details",response_model=UserReturn)
def check_user(username:str,user=Depends(get_current_user),db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == username).first()
    if not existing:
        raise HTTPException(status_code=404, detail="User Not Found")
    return {"username":existing.username, "role":existing.role}