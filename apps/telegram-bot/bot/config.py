from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    bot_token: str
    bot_api_key: str = Field(min_length=32)
    backend_url: str = "http://backend:8000/api/internal"
    redis_url: str = "redis://redis:6379/1"
    timezone: str = "Asia/Qyzylorda"
