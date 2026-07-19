"""Topic/keyword research and posting-time recommendations.

Demand signals (topic search, trending charts) come from the real, public
YouTube Data API. Posting-time recommendations use real Analytics data when
`--use-analytics` is available; otherwise they fall back to published
industry benchmarks, and the report always states which one it's giving you
so you never mistake a benchmark for a measurement of your own audience.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import youtube_data
from .config import Settings

# YouTube's official videoCategoryId values relevant to personal-finance /
# wealth-style channels. https://developers.google.com/youtube/v3/docs/videoCategories
CATEGORY_HINTS = {
    "finance": "27",       # Education
    "wealth": "27",
    "investing": "27",
    "business": "27",
    "howto": "26",         # Howto & Style
    "news": "25",          # News & Politics
    "entertainment": "24",
    "vlog": "22",           # People & Blogs
}

# Published, general US-audience benchmarks for when a Business/Education/
# finance channel's audience is typically most active. This is an industry
# heuristic, NOT a measurement — real audience timing requires OAuth
# Analytics (`ytcopilot auth`), because YouTube doesn't expose an hour-of-day
# metric via any public API.
NICHE_POSTING_BENCHMARKS = {
    "default": [
        "Tue-Thu, 7-9am ET (pre-work/commute scroll)",
        "Tue-Thu, 12-1pm ET (lunch break)",
        "Sat-Sun, 9-11am ET (weekend research/planning mode — strong for finance/wealth content)",
    ],
}


@dataclass
class TopicIdea:
    query: str
    title: str
    channel_title: str
    published_at: str
    video_id: str


def suggest_topics(settings: Settings, niche: str, region: str = "US", max_results: int = 15) -> list[TopicIdea]:
    results = youtube_data.search_topics(settings, niche, region_code=region, max_results=max_results)
    return [
        TopicIdea(
            query=niche,
            title=r["title"],
            channel_title=r["channel_title"],
            published_at=r["published_at"],
            video_id=r["video_id"],
        )
        for r in results
    ]


def trending_snapshot(settings: Settings, niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    category_id = None
    lower = niche.lower()
    for key, cat in CATEGORY_HINTS.items():
        if key in lower:
            category_id = cat
            break
    return youtube_data.trending_videos(settings, category_id=category_id, region_code=region, max_results=max_results)


def recommend_posting_schedule(settings: Settings, niche: str, use_analytics: bool) -> dict:
    if not use_analytics:
        return {
            "source": "benchmark",
            "note": (
                "No Analytics data used — this is a published US-audience benchmark for "
                "business/finance-style content, not a measurement of YOUR audience. "
                "Run `ytcopilot auth` then re-run with --use-analytics for real numbers."
            ),
            "windows": NICHE_POSTING_BENCHMARKS["default"],
        }

    from . import youtube_analytics

    audience = youtube_analytics.get_audience_by_day_and_country(settings)
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    by_day = sorted(audience["by_day"], key=lambda r: -r[1])
    top_days = [f"{r[0]} ({r[1]:,} views)" for r in by_day[:3]]
    top_countries = [f"{r[0]} ({r[1]:,} views)" for r in audience["by_country"][:5]]

    return {
        "source": "analytics",
        "note": (
            "Based on your channel's real trailing-90-day view distribution. "
            "YouTube's Analytics API has no hour-of-day dimension (that heatmap is Studio-UI-only "
            "with no API access), so pair these top days with the benchmark hour-windows below "
            "and verify precise hourly timing in YouTube Studio > Audience > 'When your viewers "
            "are on YouTube'."
        ),
        "top_days_by_views": top_days,
        "top_countries_by_views": top_countries,
        "suggested_hour_windows": NICHE_POSTING_BENCHMARKS["default"],
    }
