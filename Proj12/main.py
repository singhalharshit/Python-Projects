from fastapi import FastAPI
from auth.router import router
from db.models import Base
from db.session import engine


app = FastAPI()
Base.metadata.create_all(bind=engine)


app.include_router(router)

