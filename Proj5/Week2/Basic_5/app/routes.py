from fastapi import APIRouter, HTTPException
from models import UserCreate
import storage

router = APIRouter()


@router.post("/users")
def create_user(user: UserCreate):
    try:
        return storage.create_user(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
