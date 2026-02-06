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
    is_active = Column(Integer, default=1)

class FileUpload(Base):
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    file_type = Column(String)
    status = Column(String, default="PENDING")
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class FileResult(Base):
    __tablename__ = "file_results"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"))
    normalized_data = Column(JSON)
    error_report = Column(JSON)
    processed_at = Column(DateTime, default=datetime.utcnow)
