from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Portfolio Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    MARKET_DATA_SERVICE_URL: str = "http://market-data-service:8000"
    FORECAST_SERVICE_URL: str = "http://forecast-service:8000"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
