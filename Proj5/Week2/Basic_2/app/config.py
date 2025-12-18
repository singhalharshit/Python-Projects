import json
import os
from pathlib import Path


class AppConfig:
    def __init__(self, service_name: str, version: str, environment: str, debug: bool):
        self.service_name = service_name
        self.version = version
        self.environment = environment
        self.debug = debug


def load_config() -> AppConfig:
    """
    Loads application configuration once at startup.
    Fails fast if config is missing or invalid.
    """
    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / "config.json"

    if not config_path.exists():
        raise RuntimeError("config.json not found. Application cannot start.")

    with open(config_path) as f:
        data = json.load(f)

    try:
        return AppConfig(
            service_name=data["service_name"],
            version=data["version"],
            environment=data["environment"],
            debug=bool(data["debug"]),
        )
    except KeyError as e:
        raise RuntimeError(f"Missing required config key: {e}")
