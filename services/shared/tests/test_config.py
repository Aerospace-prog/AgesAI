"""Unit tests for ages_common.config module."""

import os

from ages_common.config import BaseServiceSettings


def test_default_settings() -> None:
    """Verify default settings are loaded correctly."""
    settings = BaseServiceSettings()

    assert settings.app_name == "ages-ai-service"
    assert settings.app_env == "development"
    assert settings.is_development is True
    assert settings.is_production is False
    assert settings.log_level == "debug"
    assert settings.embedding_dimensions == 1536


def test_env_override(monkeypatch: object) -> None:
    """Verify environment variables override defaults."""
    os.environ["APP_ENV"] = "production"
    os.environ["APP_NAME"] = "embedding-service"
    os.environ["LOG_LEVEL"] = "info"

    try:
        settings = BaseServiceSettings()
        assert settings.app_env == "production"
        assert settings.app_name == "embedding-service"
        assert settings.is_production is True
        assert settings.is_development is False
    finally:
        os.environ.pop("APP_ENV", None)
        os.environ.pop("APP_NAME", None)
        os.environ.pop("LOG_LEVEL", None)
