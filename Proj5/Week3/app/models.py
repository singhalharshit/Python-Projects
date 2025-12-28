from pydantic import BaseModel,Field
from typing import Annotated

class Product_Base(BaseModel):
    name:str
    price:Annotated[float,Field(gt=0)]
    quantity:Annotated[int,Field(ge=0)]
    
    

class Product(Product_Base):
    id:int
    created_at: str
    is_available:bool
    
    
class Stock_Adjust(BaseModel):
    quantity:Annotated[int,Field(ge=0)]
    is_available:bool