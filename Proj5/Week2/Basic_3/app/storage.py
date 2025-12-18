from typing import Dict
from models import Item, ItemCreate

_items: Dict[int, Item] = {}
_current_id: int = 0


def create_item(item_data: ItemCreate) -> Item:
    global _current_id
    _current_id += 1

    item = Item(
        id=_current_id,
        name=item_data.name,
        price=item_data.price,
        is_active=item_data.is_active
    )

    _items[item.id] = item
    return item


def get_all_items():
    return list(_items.values())


def get_item(item_id: int) -> Item | None:
    return _items.get(item_id)


def update_item(item_id: int, item_data: ItemCreate) -> Item | None:
    if item_id not in _items:
        return None

    updated_item = Item(id=item_id, **item_data.dict())
    _items[item_id] = updated_item
    return updated_item


def soft_delete_item(item_id: int) -> bool:
    if item_id not in _items:
        return False

    _items[item_id].is_active = False
    return True
