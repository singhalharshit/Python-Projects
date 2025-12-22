from fastapi import APIRouter
import storage
from models import Notes,Notes_ID


router = APIRouter()


@router.post("/Create")
def create_post(note:Notes_ID):
    return storage.create_notes(note)

@router.get("/get_all_post")
def show_all_post():
    return storage.get_all()


@router.get("/get_post_by_id")
def post_by_id(id:int):
    return storage.get_by_id(id)

@router.put("/update_post")
def update_post(id:int, item_data: Notes_ID):
    return storage.update_notes(note_id=id,note_data=item_data)

