from datetime import datetime
from fastapi import APIRouter, Depends
from config import AppConfig

router = APIRouter()


def get_config() -> AppConfig:
    """
    Dependency placeholder.
    The real config instance will be injected from main.py.
    """
    raise RuntimeError("Config dependency not initialized")


@router.get("/config")
def get_config_details(config: AppConfig = Depends(get_config)):
    response = {
        "service_name": config.service_name,
        "version": config.version,
        "environment": config.environment,
        "debug": config.debug,
    }

    if config.debug:
        response["timestamp"] = datetime.utcnow().isoformat()

    return response


@router.get("/health")
def health_check(config: AppConfig = Depends(get_config)):
    if config.environment == "development":
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }

    return {
        "status": "healthy"
    }
