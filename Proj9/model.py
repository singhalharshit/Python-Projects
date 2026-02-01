from pydantic import BaseModel

class BookCreateModel(BaseModel):
    title:str
    author:str
    publisher:str
    published_date:str
    page_count:int
    language:str
    
class bookReturnModel(BookCreateModel):
    id:int

# "id": 1,
#         "title": "Think Python",
#         "author": "Allen B. Downey",
#         "publisher": "O'Reilly Media",
#         "published_date": "2021-01-01",
#         "page_count": 1234,
#         "language": "English",