import time
from jose import JWTError,jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

SECRET_KEY="SOME_RANDOM_ACCESS_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30


oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class AuthHandler(object):
    
    @staticmethod
    def sign_jwt(user_id:int):
        payload={
            "user_id":user_id,
            "expires":time.time()+900
        }
        token = jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)
        return token
