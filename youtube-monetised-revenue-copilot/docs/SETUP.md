# Setup walkthrough

## 1. YouTube Data API key (required for everything except pure text generation)

1. Go to https://console.cloud.google.com/ and create a project (or reuse one).
2. APIs & Services > Library > enable **"YouTube Data API v3"**.
3. APIs & Services > Credentials > Create credentials > API key.
4. Put it in `.env` as `YOUTUBE_API_KEY`.

This key is free and covers `diagnose` (public stats), `research`, and the
non-analytics parts of `schedule`.

## 2. YouTube Analytics OAuth (optional, needed for `--use-analytics`)

Watch-hours, Shorts-view totals, and audience day/country breakdowns are
private to the channel owner — the API key above cannot see them.

1. In the same Google Cloud project, APIs & Services > Library > enable
   **"YouTube Analytics API"**.
2. APIs & Services > Credentials > Create credentials > OAuth client ID >
   Application type **Desktop app**.
3. Put the generated client ID/secret in `.env` as `YOUTUBE_OAUTH_CLIENT_ID`
   / `YOUTUBE_OAUTH_CLIENT_SECRET`.
4. Run `ytcopilot auth` once — it opens a browser, you sign in with the
   Google account that owns the channel, and a token is cached locally
   (`.ytcopilot_token.json`, already git-ignored).

If your OAuth consent screen is in "Testing" mode, add your own Google
account as a test user under APIs & Services > OAuth consent screen, or
publish the app (fine for personal use).

**If you'll use the web dashboard's "Connect YouTube Analytics" button**
instead of (or in addition to) `ytcopilot auth`: same client ID/secret, but
also add `http://localhost:8000/auth/callback` under that OAuth client's
**Authorized redirect URIs**. Desktop-app clients accept any port/path on
`localhost`, so this works without creating a separate "Web application"
client — just make sure `WEBAPP_OAUTH_REDIRECT_URI` in `.env` matches
whatever host/port you actually run the dashboard on.

## 3. Gemini API key (required for script/title/description/thumbnail generation)

1. https://aistudio.google.com/apikey > Create key.
2. Put it in `.env` as `GEMINI_API_KEY`.

This covers both text generation (script, titles, description, chapters,
thumbnail design brief) and rendering the actual thumbnail PNG — one key,
via `GEMINI_TEXT_MODEL` and `GEMINI_IMAGE_MODEL` in `.env`. Google AI Studio
has a free tier that doesn't require a credit card to start; you'll only
need to worry about billing if you exceed its rate limits.

## 4. Web dashboard auth (only if deploying beyond localhost)

`pip install -e ".[web]"` for `fastapi`/`uvicorn`/`jinja2`. Then set
`WEBAPP_USERNAME` and `WEBAPP_PASSWORD` in `.env` to any values you choose —
these gate every dashboard route behind HTTP Basic Auth, since every action
(script/title/thumbnail generation) uses real Gemini API quota and
an open, publicly reachable instance is a real cost risk, not just a privacy
one. Leave both blank if you're only ever running it on your own machine.

## Notes on what's genuinely not checkable via API

`ytcopilot diagnose` will list these as manual checks every time, because
YouTube does not expose them through any API to anyone but the signed-in
channel owner in Studio:

- Active Community Guidelines strikes
- 2-Step Verification status
- AdSense linkage status
- Channel country eligibility for YPP
- Advertiser-friendly / reused-content policy compliance per video

Check these directly in YouTube Studio; the report tells you exactly where.
