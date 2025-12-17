from datetime import datetime
from fastapi import APIRouter
from config import SERVICE_NAME,ENVIRONMENT,VERSION


router = APIRouter()


@router.get('/')
def root():
    return{
        "Service Name": SERVICE_NAME,
        "Version": VERSION,
        "Message": "Service is running"
        
    }
    

@router.get("/health")
def health():
    return{
        "Status": "Healthy",
        "Current_time": datetime.utcnow().isoformat()
    }



@router.get("/about")
def about():
    return {
        "service": SERVICE_NAME,
        "description": "Basic FastAPI service for learning backend fundamentals",
        "environment": ENVIRONMENT
    }