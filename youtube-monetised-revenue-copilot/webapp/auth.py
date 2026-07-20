"""Optional HTTP Basic Auth for the whole app.

Every dashboard action spends real Gemini/YouTube API quota, so
an unauthenticated deploy reachable beyond localhost is a real cost risk,
not just a privacy one. If WEBAPP_USERNAME and WEBAPP_PASSWORD are both set,
every request must match them. If either is unset, the app runs open —
fine for strictly local use, logged loudly on startup either way.
"""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from ytcopilot.config import get_settings

_security = HTTPBasic(auto_error=False)


def require_auth(credentials: HTTPBasicCredentials | None = Depends(_security)) -> None:
    settings = get_settings()
    if not settings.webapp_username or not settings.webapp_password:
        return  # auth not configured — open/local-only mode

    valid = bool(credentials) and (
        secrets.compare_digest(credentials.username, settings.webapp_username)
        and secrets.compare_digest(credentials.password, settings.webapp_password)
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def auth_is_configured() -> bool:
    settings = get_settings()
    return bool(settings.webapp_username and settings.webapp_password)
