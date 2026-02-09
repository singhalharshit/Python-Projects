from pydantic import BaseModel,EmailStr

class UserDetails(BaseModel):
    id:int
    username: str
    email: EmailStr
    
    

class UserStatus(UserDetails):
    availability_status: str
    