from fastapi import FastAPI
from config import load_config, AppConfig
from routes import router, get_config

app = FastAPI(title="Config Driven API")

# Load config ONCE at startup
app_config: AppConfig = load_config()


# Dependency override
def _get_config_override() -> AppConfig:
    return app_config


app.dependency_overrides[get_config] = _get_config_override

# Include routes
app.include_router(router)
