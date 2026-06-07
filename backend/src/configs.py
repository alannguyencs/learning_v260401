"""Application configuration settings."""

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    middleware_secret_key: str = os.getenv(
        "MIDDLEWARE_SECRET_KEY", "default-secret-key-change-in-production"
    )
    allowed_origins: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "default-jwt-secret-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    webapp_access_token: str = os.getenv("WEBAPP_ACCESS_TOKEN", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        extra = "ignore"


settings = Settings()
