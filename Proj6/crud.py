from sqlalchemy.orm import Session
from models import User
from security import hash_password


def get_user_by_email(db:Session,email:str):
    return db.query(User).filter(User.email==email).first()


def create_user(db:Session,email:str,password:str,role:str):
    exisiting = get_user_by_email(db,email)
    if exisiting:
        return ValueError("Email already Registered")
    
    user = User(
        email = email,
        hashed_password = hash_password(password),
        role= role,
        is_active = True        
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


