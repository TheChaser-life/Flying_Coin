from pydantic_settings import BaseSettings, SettingsConfigDict


class MarketDataConfig(BaseSettings):
    PROJECT_NAME: str = "Market Data Service"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"

    # Database — use asyncpg driver for async SQLAlchemy
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/db"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Consumer concurrency
    CONSUMER_PREFETCH_COUNT: int = 50

    # Redis TTL for price cache (seconds)
    REDIS_PRICE_TTL: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = MarketDataConfig()
