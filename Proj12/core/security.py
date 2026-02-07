from datetime import datetime,timedelta
from passlib.context import CryptContext
from jose import jwt,JWTError


pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

DEFAULT_TIME_OUT = 30
SECRET_KEY = "MY_VERY_SECRET_KEY"
ALGORITHM="HS256"

def hash_password(password:str):
    hashed_password = pwd_context.hash(password)
    return hashed_password

def verify_password(password,hashed_password):
    return pwd_context.verify(password,hashed_password)

def create_access_token(data:dict):
    data_copy = data.copy()
    data_copy["exp"] = datetime.utcnow() + timedelta(
        minutes=DEFAULT_TIME_OUT
    )
    return jwt.encode(data_copy, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    except JWTError:
        return None