from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import UserCreate,UserResponse, UserLogin, Token
from crud import create_user,get_user_by_email
from security import verify_password, create_access_token
from deps import get_current_user, require_admin
from models import User

app = FastAPI(title= "AUTH System")



@app.post("/login", response_model=Token)
def login(data: UserLogin,db: Session = Depends(get_db)):
    user = get_user_by_email(db, data.email)

    if not user or not verify_password(
        data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {"access_token": token}

@app.post("/register",response_model= UserResponse)
def register_user(user:UserCreate,db:Session=Depends(get_db)):
    try:
        return create_user(
            db=db,
            email=user.email,
            password=user.password,
            role=user.role
        )
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
    


@app.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/admin-only")
def admin_route(current_user: User = Depends(require_admin)):
    return {
        "message": f"Welcome Admin (user_id={current_user.id})"
    }