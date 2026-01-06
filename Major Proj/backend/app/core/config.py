"""
Centralized configuration management using Pydantic settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./app.db", env="DATABASE_URL")
    DATABASE_POOL_SIZE: int = Field(default=10, env="DATABASE_POOL_SIZE")
    
    # Redis (Optional for dev)
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # JWT Authentication
    SECRET_KEY: str = Field(default="development_secret_key_only", env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # API Keys - Free Tier (Optional now!)
    REDDIT_CLIENT_ID: str = Field(default="", env="REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET: str = Field(default="", env="REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT: str = Field(default="DecisionAssistant/1.0", env="REDDIT_USER_AGENT")
    
    YOUTUBE_API_KEY: str = Field(default="", env="YOUTUBE_API_KEY")
    
    # Optional - Premium Features
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    
    # Application Settings
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    CORS_ORIGINS: str = Field(default="*", env="CORS_ORIGINS")
    API_V1_STR: str = Field(default="/api", env="API_V1_STR")
    
    # Celery (Optional for dev)
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Rate Limiting & Resilience
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    CIRCUIT_BREAKER_THRESHOLD: int = Field(default=5, env="CIRCUIT_BREAKER_THRESHOLD")
    CIRCUIT_BREAKER_TIMEOUT: int = Field(default=60, env="CIRCUIT_BREAKER_TIMEOUT")
    
    # Instagram API Configuration
    INSTAGRAM_APP_ID: str = Field(default="", env="INSTAGRAM_APP_ID")
    INSTAGRAM_APP_SECRET: str = Field(default="", env="INSTAGRAM_APP_SECRET")
    INSTAGRAM_ACCESS_TOKEN: str = Field(default="", env="INSTAGRAM_ACCESS_TOKEN")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
