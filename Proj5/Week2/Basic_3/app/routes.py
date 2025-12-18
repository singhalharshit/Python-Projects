from fastapi import APIRouter, HTTPException
from models import ItemCreate
import storage

router = APIRouter()


@router.post("/items")
def create_item(item: ItemCreate):
    return storage.create_item(item)


@router.get("/items")
def get_items():
    return storage.get_all_items()


@router.get("/items/{item_id}")
def get_item(item_id: int):
    item = storage.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}")
def update_item(item_id: int, item: ItemCreate):
    updated = storage.update_item(item_id, item)
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@router.delete("/items/{item_id}")
def delete_item(item_id: int):
    success = storage.soft_delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deactivated"}
