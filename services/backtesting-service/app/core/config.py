from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Backtesting Engine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    MARKET_DATA_SERVICE_URL: str = "http://market-data-service:8000"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
