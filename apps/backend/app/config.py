from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    ENVIRONMENT: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Internal auth (bot -> backend)
    BOT_INTERNAL_API_KEY: str

    # File uploads
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_IMAGE_MIME_TYPES: str = "image/jpeg,image/png,image/webp"

    # Telegram bot (used by backend to push notifications)
    BOT_TOKEN: str = ""
    TELEGRAM_API_BASE: str = "https://api.telegram.org"

    # Rate limiting
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def allowed_mime_list(self) -> list[str]:
        return [m.strip() for m in self.ALLOWED_IMAGE_MIME_TYPES.split(",") if m.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
