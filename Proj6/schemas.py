from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email:EmailStr
    password:str
    role:str = "user"
    

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    role:str
    is_active:bool
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    email:EmailStr
    password:str
    

class Token(BaseModel):
    access_token:str
    token_type:str = "bearer"