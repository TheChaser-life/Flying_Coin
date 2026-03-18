from pydantic_settings import BaseSettings, SettingsConfigDict


class SentimentConfig(BaseSettings):
    PROJECT_NAME: str = "Sentiment Service"
    VERSION: str = "1.0.0"

    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    REDIS_URL: str = "redis://localhost:6379/0"

    CONSUMER_PREFETCH_COUNT: int = 10
    REDIS_SENTIMENT_TTL: int = 86400  # 24h

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


config = SentimentConfig()
