"""Environment/config loading. All keys are optional at import time so
individual commands can fail with a clear, specific error only when the
feature that needs them is actually invoked."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class MissingConfig(RuntimeError):
    """Raised when a command needs a key/credential that isn't set."""


@dataclass(frozen=True)
class Settings:
    youtube_api_key: str | None = os.getenv("YOUTUBE_API_KEY")
    oauth_client_id: str | None = os.getenv("YOUTUBE_OAUTH_CLIENT_ID")
    oauth_client_secret: str | None = os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET")
    oauth_token_path: Path = Path(os.getenv("YOUTUBE_OAUTH_TOKEN_PATH", ".ytcopilot_token.json"))
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    gemini_image_model: str = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

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

    def require_anthropic_key(self) -> str:
        if not self.anthropic_api_key:
            raise MissingConfig(
                "ANTHROPIC_API_KEY is not set. Get one at "
                "https://console.anthropic.com/settings/keys and add it to .env."
            )
        return self.anthropic_api_key

    def require_gemini_key(self) -> str:
        if not self.gemini_api_key:
            raise MissingConfig(
                "GEMINI_API_KEY is not set. Get one at https://aistudio.google.com/apikey "
                "and add it to .env. Without it, use `ytcopilot thumbnail --brief-only` "
                "to still get a design brief and hand-off prompt with no image API needed."
            )
        return self.gemini_api_key


def get_settings() -> Settings:
    return Settings()
