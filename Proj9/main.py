from fastapi import FastAPI,Header
from typing import Optional
from model import BookCreateModel,bookReturnModel    
from books_list import books      

app=FastAPI()

@app.get('/books')
async def list_books() -> dict:
    return {"list of books":books}

@app.post("/books", response_model=bookReturnModel)
async def create_a_book(data: BookCreateModel):
    new_id = max((book["id"] for book in books), default=0) + 1

    book_to_add = bookReturnModel(
        id=new_id,
        title=data.title,
        author=data.author,
        publisher=data.publisher,
        published_date=data.published_date,
        page_count=data.page_count,
        language=data.language
    )

    books.append(book_to_add.model_dump())
    return book_to_add



@app.patch("/books")
async def update_book():
    pass

@app.delete("/books/{id}")
async def delete_book(id: int):
    for index, book in enumerate(books):
        if book["id"] == id:
            books.pop(index)
            return {"message": "Book deleted"}

    return {"error": "Book not found"}

    