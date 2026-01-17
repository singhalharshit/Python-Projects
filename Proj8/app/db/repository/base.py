from sqlalchemy.orm import Session

class baseRepository:
    def __init__(self,session:Session)->None:
        self.session = session