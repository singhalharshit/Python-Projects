from pydantic import BaseModel
from typing import Optional


class Incident(BaseModel):
    id:int
    source:str
    summary:str
    descprition:Optional[str]
    severity:str
    current_status:str
    owning_group:str
    assigned_user:str
    created_at:str
    assigned_at:str
    acknowledge_at: str
    closed_at:str