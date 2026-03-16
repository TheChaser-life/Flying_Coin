"""Forecast Service config."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ForecastConfig(BaseSettings):
    PROJECT_NAME: str = "Forecast Service"
    VERSION: str = "1.0.0"
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    RABBITMQ_URL: str = "amqp://admin:admin@localhost:5672/"
    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = ForecastConfig()
