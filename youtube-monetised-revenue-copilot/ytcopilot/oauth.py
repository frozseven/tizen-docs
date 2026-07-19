"""One-time OAuth flow so ytcopilot can read *your own* private channel data
(watch hours, audience geo/day) from the YouTube Analytics API. Public stats
never need this — see youtube_data.py.
"""

from __future__ import annotations

import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from .config import Settings

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]


def get_credentials(settings: Settings) -> Credentials:
    token_path = settings.oauth_token_path
    creds: Credentials | None = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_info(json.loads(token_path.read_text()), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())
        return creds

    client_id, client_secret = settings.require_oauth_client()
    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        SCOPES,
    )
    creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds
