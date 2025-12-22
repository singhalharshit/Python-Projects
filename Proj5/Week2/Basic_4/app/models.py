from pydantic import BaseModel



class Notes(BaseModel):
    title: str
    content: str
    created_at: str
    is_archived: bool = False
    

class Notes_ID(Notes):
    id: int
