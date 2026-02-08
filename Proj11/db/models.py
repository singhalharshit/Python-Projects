from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String)

class FileUpload(Base):
    __tablename__ = "file_uploads"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    checksum = Column(String, unique=True)
    status = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class FileResult(Base):
    __tablename__ = "file_results"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"))
    success_rows = Column(JSON)
    failed_rows = Column(JSON)
