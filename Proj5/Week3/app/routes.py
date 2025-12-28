from fastapi import APIRouter,HTTPException
from models import Product_Base
from typing import Optional
from storage import create_product,get_all

router = APIRouter()

@router.post('/products')
def create_products(products_data:Product_Base):
    if products_data.quantity < 0:
        raise HTTPException(status_code= 400,detail="Product quantity less than 0 ")
    
    return create_product(products_data)


@router.get('/products/')
def fetch_all(is_available:Optional[bool]):
    return get_all(is_available)