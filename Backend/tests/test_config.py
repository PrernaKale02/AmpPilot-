"""Tests for application settings used by the assistant."""

from app.core.config import Settings


def test_gemini_settings_load_from_environment() -> None:
    settings = Settings(
        _env_file=None,
        GEMINI_API_KEY="test-key",
        GEMINI_MODEL="test-model",
        GEMINI_FALLBACK_MODELS="fallback-one,fallback-two",
    )

    assert settings.gemini_api_key == "test-key"
    assert settings.gemini_model == "test-model"
    assert settings.gemini_fallback_models == "fallback-one,fallback-two"


def test_gemini_settings_have_model_defaults_without_an_api_key() -> None:
    settings = Settings(_env_file=None)

    assert settings.gemini_api_key is None
    assert settings.gemini_model
    assert settings.gemini_fallback_models
