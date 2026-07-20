# youtube-monetised-revenue-copilot

A CLI **and a web dashboard** for **The Wealth Sheikh** (`@The.Wealth.Sheikh`)
that help diagnose why the channel isn't earning much yet, and plan upcoming
videos (script, titles, description, chapters, thumbnail) around what
actually drives watch time and subscriber growth for this specific channel.

Both interfaces are thin layers over the same `ytcopilot` package — nothing
is implemented twice. Use whichever fits: the CLI (`ytcopilot ...`) for
quick/scriptable use, or the dashboard (`webapp/`) for a browser UI. See
"Running the web dashboard" below.

## What this is, and isn't

This tool is grounded entirely in real data, real YouTube policy, and the
channel owner's own research — not generic "growth hack" advice:

- **Monetization diagnosis** checks the channel against YouTube Partner
  Program's actual published thresholds (subscribers, watch hours / Shorts
  views), using the real YouTube Data API and, optionally, the YouTube
  Analytics API for private watch-time data.
- **Content generation** (scripts, titles, descriptions, chapters,
  thumbnails) is built on `ytcopilot/channel_profile.py` — the channel's
  decoded formula (target audience, measured title patterns, hook
  structure, script-structure timing, pacing/CTA rules) derived from
  comparing real competitor titles/views/subscriber counts, including a
  same-channel, same-format A/B that showed a 27x view difference from one
  title-writing rule alone. It uses Gemini (Google AI) for both the text
  and the actual thumbnail image.
- **`ytcopilot authenticity`** checks upload practices against the pattern
  YouTube's January 2026 "inauthentic content" policy update was enforced
  against — sixteen faceless/AI channels with a combined 4.7B views
  permanently terminated (not demonetized) for template sameness, no human
  edit pass, high AI-script share, sudden topic pivots, and 10+/day uploads
  on an identical format. This is the channel owner's own risk model built
  from that pattern, not an official YouTube scoring system — but the
  underlying event is real and directly relevant to an AI-generated,
  faceless channel.
- **`ytcopilot rollout`** spreads the channel's ten target niches (AI,
  Automation, YouTube, Monetization, Investing, Productivity, Careers,
  Personal Branding, Freelancing, Entrepreneurship) across 2-3 months
  instead of all at once, weighted toward the higher-RPM clusters, to stay
  clear of the "sudden topic pivot" risk marker above.
- **Research and scheduling** use real search/trending data from the Data
  API. Posting-time recommendations are clearly labeled as either the
  channel's own measured audience data (via Analytics API) or a general
  industry benchmark — never presented as more certain than they are.

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
   for where to get each one — all are free to obtain; the Gemini API has a
   free tier with no credit card required, though heavy use can hit its
   rate limits).
4. For anything that needs `--use-analytics` (real watch-hour data, real
   posting-time data), run `ytcopilot auth` once.

See `docs/SETUP.md` for a step-by-step walkthrough including which Google
Cloud APIs to enable.

## Commands

```
ytcopilot diagnose <channel> [--use-analytics] [--out report.md]
ytcopilot research <niche> [--region US]
ytcopilot schedule <niche> [--use-analytics]
ytcopilot rollout [--months 3]
ytcopilot ideas
ytcopilot authenticity [--uploads-per-day N] [--ai-script-percent N] \
  [--human-edit-pass/--no-human-edit-pass] [--disclosure-on/--disclosure-off] \
  [--template-rotation-count N] [--new-niches-this-month N] \
  [--human-pov-stated/--no-human-pov-stated]
ytcopilot plan <topic> [--niche "<niche>"] [--length 10] [--out-dir output]
ytcopilot thumbnail <topic> --title "<title>" [--niche "<niche>"] [--brief-only]
ytcopilot auth
```

`plan` is the end-to-end command: it writes a full script (using the decoded
six-part structure and hook beats from `channel_profile.py`), derives
timestamped chapters from it, generates title options tagged by which
measured pattern they use, writes an SEO description with the chapters and
brand line embedded, breaks the script into a text-to-video shot list
(`video_prompts.md` — one paste-ready prompt per ~8-second clip, sized for
manual rendering against a Google AI Pro Flow quota rather than an
automated/paid API, since a full-length video's worth of API-generated clips
costs several times a typical monthly credit budget), and produces a
thumbnail design brief plus a rendered PNG — all via the Gemini API
(`GEMINI_API_KEY` required), saved under `output/<topic-slug>/`. It also
checks prior thumbnails under `output/` and tells the model what
compositions/palettes to avoid repeating, and appends a reminder to do the
human edit pass and run `ytcopilot authenticity` before uploading.

## Example

```
ytcopilot diagnose @The.Wealth.Sheikh --use-analytics --out report.md
ytcopilot rollout --months 3
ytcopilot ideas
ytcopilot authenticity --uploads-per-day 2 --template-rotation-count 3
ytcopilot plan "Why Can't You Just Work Harder to Get Rich?" \
  --niche "AI/Automation" --length 9
```

## Running the web dashboard

```
pip install -e ".[web]"
uvicorn webapp.app:app --reload
```

Then open `http://localhost:8000`. Pages: Dashboard (config/auth status),
Diagnose, Research, Schedule, Rollout, Ideas, Authenticity, and Plan a video
(runs the same 6-step pipeline as `ytcopilot plan`, with live progress and
generated assets/downloads on the page when done — it writes to the same
`output/<topic-slug>/` folder the CLI uses).

**Security note:** every dashboard action spends real API credits. If you
run this anywhere reachable beyond your own machine, set `WEBAPP_USERNAME`
and `WEBAPP_PASSWORD` in `.env` first — the app then requires HTTP Basic
Auth on every request and prints a warning on startup if they're unset.
Strictly local use (`http://localhost`) is fine without them.

YouTube Analytics can be connected from the dashboard itself (Dashboard →
"Connect YouTube Analytics") instead of running `ytcopilot auth` — same
underlying OAuth client and token file, just a proper browser redirect flow
instead of the CLI's local-server flow.

### Installing it as an app (mobile + desktop)

The dashboard is a Progressive Web App — deployed somewhere reachable
(not just `localhost`), it can be "installed" from the browser on your
phone and your Windows laptop, giving it a real app icon and its own
window. See `docs/DEPLOY.md` for the full walkthrough (deploying to
Render's free tier, then installing on both devices).

## Tests

```
pytest
```
