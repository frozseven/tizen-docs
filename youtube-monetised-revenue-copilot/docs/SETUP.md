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

## 3. Anthropic API key (required for script/title/description/thumbnail-brief generation)

1. https://console.anthropic.com/settings/keys > Create key.
2. Put it in `.env` as `ANTHROPIC_API_KEY`.

This is metered/paid per request once you start generating content.

## 4. Gemini API key (optional, only for rendering actual thumbnail PNGs)

1. https://aistudio.google.com/apikey > Create key.
2. Put it in `.env` as `GEMINI_API_KEY`.

Without this, `ytcopilot thumbnail` and `ytcopilot plan` still produce a
full design brief and a ready-to-paste image-generation prompt — you just
won't get a rendered file automatically.

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
