from fastapi import FastAPI
from auth.router import router as auth_router
from files.router import router as file_router

app = FastAPI(title="Universal Ingestion Platform")

app.include_router(auth_router)
app.include_router(file_router)
