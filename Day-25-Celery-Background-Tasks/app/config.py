# ============================================================
# app/config.py
# Application configuration
# ============================================================

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Redis
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.environ.get(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND: str = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/2"
    )

    # App
    APP_NAME: str = os.environ.get("APP_NAME", "Task Manager")
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    TIMEZONE: str = os.environ.get("TIMEZONE", "Asia/Karachi")

    # Email
    EMAIL_ENABLED: bool = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    SMTP_HOST: str = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: str = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD: str = os.environ.get("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.environ.get("FROM_EMAIL", "noreply@taskmanager.com")


config = Config()