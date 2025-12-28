from models import Product,Product_Base
from typing import Dict
from datetime import datetime

_id = 0
_product: Dict[int,Product] = {}


def create_product(product_values:Product_Base)->Product:
    global _id 
    _id +=1
    
    product_details= Product(
        id = _id,
        name = product_values.name,
        price = product_values.price,
        quantity=product_values.quantity,
        created_at= datetime.utcnow().isoformat(),
        is_available= True       
        
    )
    
    _product[product_details.id]=product_details
    return product_details


def get_all(is_available:bool | None=None):
    
    
    product_values = list(_product.values())
    if is_available is None:
        return product_values
    
    return [i for i in product_values if i.is_available==is_available]
    