from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    BOT_TOKEN: str
    BACKEND_API_BASE_URL: str = "http://backend:8000/api"
    BOT_INTERNAL_API_KEY: str
    REDIS_URL: str = "redis://redis:6379/1"
    USE_REDIS_FSM_STORAGE: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
