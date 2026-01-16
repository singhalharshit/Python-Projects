from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.util.init_db import create_tables

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Created")
    create_tables()
    yield

app=FastAPI(lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"Status":"200 Ok"}