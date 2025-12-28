from pydantic import BaseModel
from typing import Optional


class ReportName(BaseModel):
    name:str


class Report(ReportName):
    id: int
    status: str
    content: Optional[str] = None
    created_at: str