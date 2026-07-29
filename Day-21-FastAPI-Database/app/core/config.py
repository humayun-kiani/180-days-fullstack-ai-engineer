# ============================================================
# app/core/config.py
# Application configuration via Pydantic Settings
# ============================================================

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All values can be overridden via .env file or shell environment.
    Pydantic validates types automatically — if POSTGRES_PORT is "5432",
    it becomes an integer automatically.
    """

    # ─── Database ─────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "taskmanager"
    POSTGRES_USER: str = "taskuser"
    POSTGRES_PASSWORD: str = "taskpass"

    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ─── Application ──────────────────────────────────────────
    APP_NAME: str = "Task Manager API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api/v1"

    # ─── Pagination ───────────────────────────────────────────
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()


# Module-level singleton
settings = get_settings()