from fastapi import FastAPI,Header,status,HTTPException
from typing import Optional
from model import BookCreateModel,bookReturnModel,BookUpdateModel
from books_list import books      

app=FastAPI()

@app.get('/books')
async def list_books() -> dict:
    return {"list of books":books}

@app.post("/books", response_model=bookReturnModel,status_code=status.HTTP_201_CREATED)
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



@app.patch("/books/{book_id}")
async def update_book(book_id: int, data: BookUpdateModel):
    for index, book in enumerate(books):
        if book["id"] == book_id:
            updated_data = book.copy()

            for key, value in data.model_dump(exclude_unset=True).items():
                updated_data[key] = value

            books[index] = updated_data
            return updated_data

    raise HTTPException(status_code=404, detail="Book not found")


@app.delete("/books/{id}")
async def delete_book(id: int):
    for index, book in enumerate(books):
        if book["id"] == id:
            books.pop(index)
            return {"message": "Book deleted"}

    return {"error": "Book not found"}

    