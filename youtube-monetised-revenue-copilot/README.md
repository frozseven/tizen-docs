# youtube-monetised-revenue-copilot

A CLI that helps diagnose why a YouTube channel isn't monetized yet, and
plans upcoming videos (script, titles, description, chapters, thumbnail)
around what actually drives watch time and subscriber growth.

## What this is, and isn't

This tool is grounded entirely in real data and real YouTube policy:

- **Monetization diagnosis** checks your channel against YouTube Partner
  Program's actual published thresholds (subscribers, watch hours / Shorts
  views), using the real YouTube Data API and, optionally, the YouTube
  Analytics API for your own private watch-time data.
- **Research and scheduling** use real search/trending data from the Data
  API. Posting-time recommendations are clearly labeled as either your own
  measured audience data (via Analytics API) or a general industry
  benchmark — never presented as more certain than they are.
- **Content generation** (scripts, titles, descriptions, chapters,
  thumbnails) uses Claude (Anthropic API) and Gemini (Google AI, for the
  actual thumbnail image).

What it will **not** do, because no honest tool can:

- **Guarantee** monetization, a specific view count, or subscriber count.
  Those depend on YouTube's algorithm and real audience behavior, not
  software.
- **Guarantee "no strikes."** Strikes come from YouTube's own policy
  enforcement. This tool flags the parts of your channel that are common
  strike/demonetization risks (misleading titles/thumbnails, reused
  content) so you can avoid them, but it cannot see or control YouTube's
  enforcement decisions.
- **Check strike status, AdSense linkage, or 2FA status.** These are private
  to the signed-in channel owner and are not exposed by any YouTube API.
  `ytcopilot diagnose` lists these explicitly as manual checks with exact
  steps in YouTube Studio.
- **Generate deliberately misleading thumbnails/titles.** Thumbnails are
  designed for high, honest CTR — accurately representing the video. YouTube
  actively suppresses reach and issues strikes for clickbait/misleading
  metadata, so bait-designed assets would work against the actual goal.

## Setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -e ".[dev]"`
3. `cp .env.example .env` and fill in the keys you need (see `.env.example`
   for where to get each one — all are free to obtain, though the Anthropic
   and Gemini APIs are metered/paid per use once you start generating
   content).
4. For anything that needs `--use-analytics` (real watch-hour data, real
   posting-time data), run `ytcopilot auth` once.

See `docs/SETUP.md` for a step-by-step walkthrough including which Google
Cloud APIs to enable.

## Commands

```
ytcopilot diagnose <channel> [--use-analytics] [--out report.md]
ytcopilot research <niche> [--region US]
ytcopilot schedule <niche> [--use-analytics]
ytcopilot plan <topic> --niche "<niche>" [--length 10] [--out-dir output]
ytcopilot thumbnail <topic> --niche "<niche>" --title "<title>" [--brief-only]
ytcopilot auth
```

`plan` is the end-to-end command: it writes a full script, derives
timestamped chapters from it, generates title options, writes an SEO
description with the chapters embedded, and produces a thumbnail design
brief plus a rendered PNG (skipped gracefully if `GEMINI_API_KEY` isn't
set) — all saved under `output/<topic-slug>/`.

## Example

```
ytcopilot diagnose @the.wealth.sheikh --use-analytics --out report.md
ytcopilot research "personal finance" --region US
ytcopilot schedule "personal finance" --use-analytics
ytcopilot plan "3 signs your bank account is losing you money" \
  --niche "personal finance" --length 8
```

## Tests

```
pytest
```
