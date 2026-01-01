from fastapi import APIRouter,status,Depends
from sqlalchemy.orm import Session


router = APIRouter(prefix="/user",tags=["users"],responses={404:{"description":"Not Found"}})

@router.post('', status_code=status.HTTP_201_CREATED)
async def create_user(data:CreateUserRequest, db:Session = Depends(get_db)):
    


