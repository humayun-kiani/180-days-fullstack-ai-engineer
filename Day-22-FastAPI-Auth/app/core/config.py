# ============================================================
# app/core/config.py — Updated with auth settings
# ============================================================

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Database ─────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "taskmanager"
    POSTGRES_USER: str = "taskuser"
    POSTGRES_PASSWORD: str = "taskpass"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── JWT / Auth ───────────────────────────────────────────
    SECRET_KEY: str = "change-this-in-production-use-secrets-token-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Redis ────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ─── Application ──────────────────────────────────────────
    APP_NAME: str = "Task Manager API"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()