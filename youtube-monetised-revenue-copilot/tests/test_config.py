import os

from ytcopilot.config import Settings, get_settings


def test_settings_rereads_env_on_each_call(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "first-value")
    assert Settings().youtube_api_key == "first-value"

    monkeypatch.setenv("YOUTUBE_API_KEY", "second-value")
    assert Settings().youtube_api_key == "second-value"


def test_get_settings_reflects_unset_var(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert get_settings().gemini_api_key is None

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    assert get_settings().gemini_api_key == "test-key"


def test_webapp_auth_settings_default_none(monkeypatch):
    monkeypatch.delenv("WEBAPP_USERNAME", raising=False)
    monkeypatch.delenv("WEBAPP_PASSWORD", raising=False)
    settings = get_settings()
    assert settings.webapp_username is None
    assert settings.webapp_password is None
