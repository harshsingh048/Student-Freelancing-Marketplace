"""
config/settings.py
──────────────────
Central configuration loaded from .env via pydantic-settings.
All other modules import `settings` from here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:Ha12@localhost:5432/student_marketplace"

    # ── JWT ─────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── App ─────────────────────────────────────────────────────────────────
    APP_NAME: str = "Student Freelancing Marketplace"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── File uploads ────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5

    # ── Mock Payment (Razorpay) ──────────────────────────────────────────────
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"
    PLATFORM_FEE_PERCENT: float = 10.0

    # ── Admin seed account ──────────────────────────────────────────────────
    ADMIN_EMAIL: str = "admin@marketplace.com"
    ADMIN_PASSWORD: str = "Ha12"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance – import this everywhere."""
    return Settings()


settings = get_settings()
