from fastapi import APIRouter, HTTPException
from models import UserCreate
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
def user_by_id(id:int):
    return storage.user_list(id)