from fastapi import APIRouter,Depends,UploadFile,HTTPException
from core.dependencies import get_current_user,require_roles
from db.session import get_db
from sqlalchemy.orm import Session
from files.model import UserUpdate
from db.models import User

router =APIRouter(prefix="/files")


@router.patch("/update_user")
def update_user(user_id: int,data:UserUpdate,db:Session = Depends(get_db),user=Depends(require_roles(["admin"]))):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.username is not None:
        user.username = data.username

    if data.role is not None:
        user.role = data.role

    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "username": user.username,
        "role": user.role
    }
    

@router.delete("/update_user")
def delete_user(user_id:int,db:Session = Depends(get_db),user=Depends(require_roles(["admin"]))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404,detail="User Not found")
    db.delete(user)
    db.commit()
    # db.refresh(user)
    
    return {
        "message":"User Deleted"
    }