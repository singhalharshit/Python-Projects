from pydantic import BaseModel,EmailStr
from typing import Union

class userCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    
class userOutput(BaseModel):
    id:int
    first_name: str
    last_name: str
    email: EmailStr

class UserInUpdate(BaseModel):
    id:int
    first_name: Union[str,None] = None
    last_name: Union[str,None] = None
    email: Union[EmailStr,None] = None
    password: Union[str,None] = None
    
class userInLogin(BaseModel):
    email:EmailStr
    password:str

class userWithToken(BaseModel):
    token:str
    
 
    
