# auth/router

from sqlalchemy.orm import Session
from db.session import get_db
from db.models import User
from core.security import verify_password


def authenticate_user(username,password,db:Session):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user
