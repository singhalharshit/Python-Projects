from pydantic import BaseModel
from typing import Optional

class UserUpdate(BaseModel):
    username:Optional[str] = None
    role:Optional[str] = None
    