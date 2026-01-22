from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"],deprecated = "auto")

class HashHelper(object):
    @staticmethod
    def verify_password(plain_password:str, hashed_password:str):
        return pwd_context.verify(plain_password,hashed_password)

    
    @staticmethod
    def hash_password(plain_password:str):
        return pwd_context.hash(plain_password)