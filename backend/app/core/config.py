from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "HireFlow Intelligence API"
    database_url: str = "sqlite:///./hireflow.db"
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()
