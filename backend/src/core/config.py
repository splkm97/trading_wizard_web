"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/trading_wizard"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: str

    # Logging
    LOG_LEVEL: str = "INFO"

    # Redis Cache
    REDIS_URL: str | None = None  # Optional: redis://localhost:6379/0
    SIGNAL_CACHE_TTL_SECONDS: int = 300  # 5 minutes (extended for stale-while-revalidate)
    SIGNAL_STALE_THRESHOLD_SECONDS: int = 60  # Consider stale after 1 minute
    PRICE_CACHE_TTL_SECONDS: int = 30  # 30 seconds

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
