from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Course Summary Generator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Storage
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/app.db"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_URL: str = "redis://localhost:6379/0"

    # Web Scraping
    REQUEST_TIMEOUT: int = 30
    MAX_RETRY: int = 3

    # Image
    DEFAULT_IMAGE_WIDTH: int = 1200
    DEFAULT_IMAGE_HEIGHT: int = 1600

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
