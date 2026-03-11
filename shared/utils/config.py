import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class SharedConfig(BaseSettings):
    """
    Common configurations across all services.
    Can be loaded from .env file or environment variables.
    """
    PROJECT_NAME: str = "Market Data Mining & Forecasting System"
    ENVIRONMENT: str = "local"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/db"
    
    # Message Broker
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    
    # Cache
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT Security (Should be overridden in production)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

config = SharedConfig()
