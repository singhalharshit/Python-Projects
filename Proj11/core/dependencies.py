from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

def require_roles(allowed_roles: list):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker
