from models import Product,Product_Base,Stock_Adjust
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
    
    
def get_product_by_id(id:int):
    return _product.get(id)


def update_product(id:int,update_item:Product_Base)-> Product:
    
    updated_data = Product(
        id=id,
        name= update_item.name,
        price= update_item.price,
        quantity= update_item.quantity,
        created_at=datetime.utcnow().isoformat(),
        is_available= True
    )
    _product[id]=updated_data
    return updated_data
    
    
def delta(id:int,delta:int)->Product:
    
    product_info=_product[id]
    quantity = _product[id].quantity
    availability = _product[id].is_available
    
    total_quantity = delta+quantity
    if total_quantity<0:
        total_quantity=0
        availability = False
    
    product_delta = Stock_Adjust(quantity=total_quantity,is_available=availability)
    final_product= Product(
        id=id,
        name=product_info.name,
        price=product_info.price,
        quantity=product_delta.quantity,
        created_at=datetime.utcnow().isoformat(),
        is_available=product_delta.is_available
    )
    
    _product[id]=final_product
    return final_product
        