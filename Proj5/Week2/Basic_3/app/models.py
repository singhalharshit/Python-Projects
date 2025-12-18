from pydantic import BaseModel


class ItemCreate(BaseModel):
    name: str
    price: float
    is_active: bool = True


class Item(ItemCreate):
    id: int
