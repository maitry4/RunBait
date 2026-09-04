"""
Application settings loaded from .env via pydantic-settings.
All environment variables used by the backend are defined here.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # GitHub OAuth App
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    # JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # GitHub personal token (optional, for repo context)
    GITHUB_TOKEN: str = ""

    # Gemini / Google AI
    GEMINI_API_KEY: str = ""

    # URLs (no trailing slash)
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
