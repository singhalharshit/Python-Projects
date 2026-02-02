from pydantic import BaseModel
from typing import Optional

class BookCreateModel(BaseModel):
    title:str
    author:str
    publisher:str
    published_date:str
    page_count:int
    language:str
    
class bookReturnModel(BookCreateModel):
    id:int


class BookUpdateModel(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    page_count: Optional[int] = None
    language: Optional[str] = None


# "id": 1,
#         "title": "Think Python",
#         "author": "Allen B. Downey",
#         "publisher": "O'Reilly Media",
#         "published_date": "2021-01-01",
#         "page_count": 1234,
#         "language": "English",