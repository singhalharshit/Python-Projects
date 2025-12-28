from fastapi import APIRouter,HTTPException
from models import Product_Base
from typing import Optional
from storage import create_product,get_all,get_product_by_id,update_product,delta

router = APIRouter()

@router.post('/products')
def create_products(products_data:Product_Base):
    if products_data.quantity < 0:
        raise HTTPException(status_code= 400,detail="Product quantity less than 0 ")
    
    return create_product(products_data)


@router.get('/products/')
def fetch_all(is_available:Optional[bool]):
    return get_all(is_available)


@router.get('/products/{id}')
def get_by_id(id:int):
    product_id = get_product_by_id(id)
    if not product_id:
        raise HTTPException(status_code=404,detail="id not found")
    
    return product_id 


@router.put('/products/{id}')
def updated_item(id:int,updated_values:Product_Base):
    product_id = get_product_by_id(id)
    
    if not product_id:
        raise HTTPException(status_code=404,detail="Id not found")

    if updated_values.quantity<0:
        raise HTTPException(status_code=404,detail="Quantity can't be 0")
    else:
        return update_product(id,updated_values)
    
    
@router.post('/products/{id}/adjust-stock')
def stock_adjust(id:int,deltas:int):
    id_check= get_product_by_id(id)
    if not id_check:
        raise HTTPException(status_code=404,detail="Id not found")
    return delta(id,deltas)