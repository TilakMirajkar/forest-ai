from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Forest AI"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://forest:forest@localhost:5432/forest_ai"
    secret_key: str = ""
    access_token_expire_minutes: int = 30
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"


@lru_cache
def get_settings() -> Settings:
    return Settings()