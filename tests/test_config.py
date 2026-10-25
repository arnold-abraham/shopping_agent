from pathlib import Path

import pytest

from shopping_agent.config import ConfigError, get_settings, require_api_key


def test_defaults(monkeypatch):
    for var in ("STORE_DB_PATH", "OPENAI_MODEL", "OPENAI_API_KEY", "LOG_LEVEL"):
        monkeypatch.delenv(var, raising=False)

    settings = get_settings()

    assert settings.db_path == Path("store.db")
    assert settings.openai_model == "gpt-4o"
    assert settings.openai_api_key is None
    assert settings.log_level == "INFO"


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("STORE_DB_PATH", "/data/shop.db")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LOG_LEVEL", "debug")

    settings = get_settings()

    assert settings.db_path == Path("/data/shop.db")
    assert settings.openai_model == "gpt-4o-mini"
    assert settings.log_level == "DEBUG"


def test_require_api_key_returns_key():
    assert require_api_key(get_settings()) == "test-key"


@pytest.mark.parametrize("value", [None, ""])
def test_require_api_key_raises_when_missing(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("OPENAI_API_KEY")
    else:
        monkeypatch.setenv("OPENAI_API_KEY", value)

    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        require_api_key(get_settings())
