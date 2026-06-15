"""Application configuration, loaded from environment variables only.

Secrets (e.g. the Anthropic API key) are read exclusively from the environment
or a local ``.env`` file that is never committed. See ``.env.example``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (this file lives in backend/app/config.py)
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


class Settings(BaseSettings):
    """Typed application settings.

    Most variables use the ``PULSE_`` prefix (e.g. ``PULSE_DATABASE_URL``).
    The Anthropic key keeps its conventional unprefixed name via an alias.
    """

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_prefix="PULSE_",
        extra="ignore",
        case_sensitive=False,
    )

    # Database. SQLite locally; a postgresql:// URL in production.
    database_url: str = f"sqlite:///{BACKEND_DIR / 'pulse.db'}"

    # CORS: which browser origins may call the API.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Default per-client rate limit applied to data routes.
    rate_limit: str = "60/minute"

    # Claude "Explain this chart" feature (Phase 3).
    # Setting an explicit alias makes pydantic-settings ignore env_prefix for
    # this field, so it is read from ANTHROPIC_API_KEY (the conventional name).
    anthropic_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY", "PULSE_ANTHROPIC_API_KEY"),
    )
    # Read from PULSE_ANTHROPIC_MODEL via the prefix.
    anthropic_model: str = "claude-haiku-4-5"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow a comma-separated string in the env var."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def anthropic_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Cached so the ``.env`` file is parsed once. Tests that need to change the
    environment can call ``get_settings.cache_clear()``.
    """
    return Settings()


settings = get_settings()
