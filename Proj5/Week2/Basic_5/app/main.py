from fastapi import FastAPI
from routes import router

app=FastAPI(title="User Management")
app.include_router(router)