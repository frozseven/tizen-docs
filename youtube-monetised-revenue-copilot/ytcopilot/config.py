"""Environment/config loading. All keys are optional at import time so
individual commands can fail with a clear, specific error only when the
feature that needs them is actually invoked."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class MissingConfig(RuntimeError):
    """Raised when a command needs a key/credential that isn't set."""


@dataclass(frozen=True)
class Settings:
    # default_factory (not a bare `= os.getenv(...)`) so each Settings() call
    # re-reads the environment instead of freezing whatever os.environ held
    # the moment this module was first imported — matters both for tests
    # that set env vars per-case and for the web app, which stays in one
    # long-lived process rather than the CLI's one-shot-per-invocation.
    youtube_api_key: str | None = field(default_factory=lambda: os.getenv("YOUTUBE_API_KEY"))
    oauth_client_id: str | None = field(default_factory=lambda: os.getenv("YOUTUBE_OAUTH_CLIENT_ID"))
    oauth_client_secret: str | None = field(default_factory=lambda: os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET"))
    oauth_token_path: Path = field(
        default_factory=lambda: Path(os.getenv("YOUTUBE_OAUTH_TOKEN_PATH", ".ytcopilot_token.json"))
    )
    gemini_api_key: str | None = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_text_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    )
    gemini_image_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    )
    webapp_username: str | None = field(default_factory=lambda: os.getenv("WEBAPP_USERNAME"))
    webapp_password: str | None = field(default_factory=lambda: os.getenv("WEBAPP_PASSWORD"))
    webapp_oauth_redirect_uri: str = field(
        default_factory=lambda: os.getenv("WEBAPP_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/callback")
    )

    def require_youtube_api_key(self) -> str:
        if not self.youtube_api_key:
            raise MissingConfig(
                "YOUTUBE_API_KEY is not set. Get a free key at "
                "https://console.cloud.google.com/apis/credentials (enable 'YouTube Data API v3' "
                "first), then add it to your .env file."
            )
        return self.youtube_api_key

    def require_oauth_client(self) -> tuple[str, str]:
        if not self.oauth_client_id or not self.oauth_client_secret:
            raise MissingConfig(
                "YOUTUBE_OAUTH_CLIENT_ID / YOUTUBE_OAUTH_CLIENT_SECRET are not set. "
                "Create a Desktop-app OAuth client in the same Google Cloud project "
                "(enable 'YouTube Analytics API'), then add both values to .env and "
                "run `ytcopilot auth`."
            )
        return self.oauth_client_id, self.oauth_client_secret

    def require_gemini_key(self) -> str:
        if not self.gemini_api_key:
            raise MissingConfig(
                "GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey "
                "and add it to .env. Required for script/title/description/chapter/thumbnail-brief "
                "generation and for rendering the thumbnail image."
            )
        return self.gemini_api_key


def get_settings() -> Settings:
    return Settings()
