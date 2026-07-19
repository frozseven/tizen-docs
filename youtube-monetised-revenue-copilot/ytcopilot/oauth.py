"""One-time OAuth flow so ytcopilot can read *your own* private channel data
(watch hours, audience geo/day) from the YouTube Analytics API. Public stats
never need this — see youtube_data.py.
"""

from __future__ import annotations

import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow, InstalledAppFlow

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


def build_web_flow(settings: Settings, redirect_uri: str, *, code_verifier: str | None = None) -> Flow:
    """Authorization Code flow for the web dashboard's /auth/start + /auth/callback
    routes — separate from get_credentials' local-server flow used by `ytcopilot auth`.
    Needs a "Web application" type OAuth client (not the Desktop-app one used by
    `ytcopilot auth`), since Google's loopback exception for arbitrary redirect URIs
    only covers localhost, not a real hosted domain.

    Google requires PKCE for this client type: /auth/start generates a code_verifier
    (via autogenerate_code_verifier) and must hand it back in here on /auth/callback
    so the token exchange uses the same one — a fresh Flow object with no verifier at
    all produces "invalid_grant: Missing code verifier" from Google's token endpoint.
    """
    client_id, client_secret = settings.require_oauth_client()
    return Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        code_verifier=code_verifier,
        autogenerate_code_verifier=code_verifier is None,
    )


# In-memory store bridging /auth/start's generated code_verifier to /auth/callback,
# keyed by the OAuth `state` param — the two routes build separate Flow objects
# (one per request) so the verifier can't just live on a single Flow instance.
_pending_code_verifiers: dict[str, str] = {}


def store_code_verifier(state: str, code_verifier: str) -> None:
    _pending_code_verifiers[state] = code_verifier


def pop_code_verifier(state: str | None) -> str | None:
    if not state:
        return None
    return _pending_code_verifiers.pop(state, None)


def save_credentials(settings: Settings, creds: Credentials) -> None:
    settings.oauth_token_path.write_text(creds.to_json())


def has_saved_credentials(settings: Settings) -> bool:
    return settings.oauth_token_path.exists()
