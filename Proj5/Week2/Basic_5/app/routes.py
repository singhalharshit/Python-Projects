#routes.py

from fastapi import APIRouter, HTTPException
from models import UserCreate,UserUpdate
from typing import Optional
import storage

router = APIRouter()


@router.post("/users")
def create_user(user: UserCreate):
    try:
        return storage.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/user")
def get_user(is_active:Optional[bool]):
    return storage.all_active_user(is_active)


@router.get("/users/{id}")
def user_by_id(id: int):
    user = storage.get_user_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user




@router.put("/users/{id}")
def update_user(id: int, user: UserUpdate):
    try:
        updated = storage.update_user(id, user)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))