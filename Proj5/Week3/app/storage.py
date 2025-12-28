# storage.py

from models import Product,Product_Base,Stock_Adjust
from typing import Dict
from datetime import datetime

_id = 0
_product: Dict[int,Product] = {}


def create_product(product_values: Product_Base) -> Product:
    global _id
    _id += 1

    is_available = product_values.quantity > 0

    product = Product(
        id=_id,
        name=product_values.name,
        price=product_values.price,
        quantity=product_values.quantity,
        created_at=datetime.utcnow().isoformat(),
        is_available=is_available
    )

    _product[product.id] = product
    return product


def get_all(is_available:bool | None=None):
    product_values = list(_product.values())
    if is_available is None:
        return product_values
    
    return [i for i in product_values if i.is_available==is_available]
    
    
def get_product_by_id(id:int):
    return _product.get(id)


def update_product(id: int, update_item: Product_Base) -> Product | None:
    if id not in _product:
        return None

    existing = _product[id]

    existing.name = update_item.name
    existing.price = update_item.price
    existing.quantity = update_item.quantity
    existing.is_available = update_item.quantity > 0

    return existing
    
    
def adjust_stock(id: int, delta: int) -> Product | None:
    if id not in _product:
        return None

    product = _product[id]
    new_quantity = product.quantity + delta

    if new_quantity < 0:
        raise ValueError("Stock adjustment would make quantity negative")

    product.quantity = new_quantity
    product.is_available = new_quantity > 0

    return product

        