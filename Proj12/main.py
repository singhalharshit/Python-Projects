from fastapi import FastAPI
from auth.router import router
from db.models import Base
from db.session import engine
from files.router import router as FileRouter


app = FastAPI()
Base.metadata.create_all(bind=engine)


app.include_router(router)
app.include_router(FileRouter)

