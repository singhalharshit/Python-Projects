# db/models

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer,String,DateTime,ForeignKey
from datetime import datetime


Base = declarative_base()

class User(Base):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password = Column(String)
    role = Column(String(25),default="Viewer")
    created_on = Column(DateTime,default=datetime.utcnow) 

# class FileUpload(Base):
#     __tablename__ = "file_uploads"

#     id = Column(Integer, primary_key=True)
#     filename = Column(String)
#     file_type = Column(String)
#     status = Column(String, default="PENDING")
#     uploaded_by = Column(Integer, ForeignKey("users.id"))
#     created_at = Column(DateTime, default=datetime.utcnow)