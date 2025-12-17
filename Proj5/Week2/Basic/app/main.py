from fastapi  import FastAPI
from routes import router


app = FastAPI(title="Hello Backend")


app.include_router(router)