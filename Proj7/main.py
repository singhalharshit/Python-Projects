from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel,EmailStr
from typing import Dict
from datetime import datetime, timedelta
from jose import JWTError,jwt
from passlib.context import CryptContext

SECRET_KEY="SOME_RANDOM_ACCESS_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30



fake_db =  {
    "user1":{
        "username":"user_1",
        "full_name":"User One",
        "email": "user_one@user.com",
        "hashed_password":"",
        "disabled":"False"            
    }
}


class Token(BaseModel):
    access_token:str
    token_type:str
    
class TokenData(BaseModel):
    username:str or None = None
    
class User(BaseModel):
    username:str
    email:EmailStr or None = None
    full_name:str or None = None
    disabled: bool or None = None
    
class UserInDB(User):
    hashed_password:str
    
    
pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app=FastAPI()

def verify_password(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def get_passowrd_hash(password):
    return pwd_context.hash(password)

def get_user(db,username:str):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)
    

def authenticate_user(db,username:str, password:str):
    user = get_user(db,username)
    if not user:
        return False

    if not verify_password(password,user.hashed_password):
        return False
    
    return user 


def create_access_token(data:dict,expires_delta:timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expires = datetime.utcnow()+expires_delta
    else:
        expires = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode.update({"exp":expires})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token:str = Depends(oauth_2_scheme)):
    