from fastapi import FastAPI
from routes import router


app=FastAPI(title = "CRUD API")
app.include_router(router)