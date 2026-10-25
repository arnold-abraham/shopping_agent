"""Runtime settings, read from environment variables (and a local .env file)."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB_PATH = "store.db"
DEFAULT_MODEL = "gpt-4o"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    db_path: Path
    openai_model: str
    openai_api_key: str | None
    log_level: str


def get_settings() -> Settings:
    """Read settings from the environment on every call, so tests can override them."""
    return Settings(
        db_path=Path(os.getenv("STORE_DB_PATH", DEFAULT_DB_PATH)),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )


def require_api_key(settings: Settings) -> str:
    if not settings.openai_api_key:
        raise ConfigError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return settings.openai_api_key


def configure_logging() -> None:
    logging.basicConfig(
        level=get_settings().log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
