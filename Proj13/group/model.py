from pydantic import BaseModel
from typing import List

class Group(BaseModel):
    id:int
    group_name:str
    list_of_users:List[str]
    default_assignment:str