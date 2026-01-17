from .base import baseRepository
from app.db.models.user import User
from app.db.schema.user import userCreate





class UserRepository(baseRepository):
    def create_user(self,user_data:userCreate):
        newUser = User(user_data.model_dump(exclude_none=True))
        self.session.add(instance=newUser)
        self.session.commit()
        self.session.refresh(instance=newUser)
        
        return newUser   
    
    def user_exists_by_email(self,email:str) -> bool:
        user=self.session.query(User).filter_by(email=email).first()
        return bool(user)
    
    
    def get_user_by_email(self,email:str) -> str:
        user=self.session.query(User).filter_by(email=email).first()
        return user
    
    def get_user_by_id(self,user_id:int):
        user=self.session.query(User).filter_by(id=user_id).first()
        return user 
            
        