"""YouTube Analytics API (OAuth) — the only source for data that's private
to the channel owner: watch-hour totals, Shorts view totals, and audience
day/geo distribution. Requires `ytcopilot auth` to have been run once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from googleapiclient.discovery import build

from .config import Settings
from .oauth import get_credentials

MINE = "channel==MINE"


def _client(settings: Settings):
    creds = get_credentials(settings)
    return build("youtubeAnalytics", "v2", credentials=creds)


@dataclass
class WatchHourSummary:
    trailing_365d_watch_hours: float
    trailing_90d_shorts_views: int
    trailing_365d_views: int


def get_watch_hour_summary(settings: Settings) -> WatchHourSummary:
    client = _client(settings)
    today = date.today()

    year_resp = client.reports().query(
        ids=MINE,
        startDate=(today - timedelta(days=365)).isoformat(),
        endDate=today.isoformat(),
        metrics="estimatedMinutesWatched,views",
    ).execute()
    row = year_resp.get("rows", [[0, 0]])[0]
    watch_hours = row[0] / 60.0
    views_365d = int(row[1])

    shorts_resp = client.reports().query(
        ids=MINE,
        startDate=(today - timedelta(days=90)).isoformat(),
        endDate=today.isoformat(),
        metrics="views",
        dimensions="creatorContentType",
    ).execute()
    shorts_views = 0
    for r in shorts_resp.get("rows", []):
        if r[0] == "SHORTS":
            shorts_views = int(r[1])

    return WatchHourSummary(
        trailing_365d_watch_hours=round(watch_hours, 1),
        trailing_90d_shorts_views=shorts_views,
        trailing_365d_views=views_365d,
    )


def get_audience_by_day_and_country(settings: Settings, days: int = 90) -> dict:
    """Returns raw views-by-day-of-week and views-by-country. YouTube's
    Analytics API does not expose an hour-of-day dimension at all (that
    heatmap only exists inside Studio's UI, with no public API), so this is
    the closest real signal available: which days your audience actually
    watches, and where they're located.
    """
    client = _client(settings)
    today = date.today()
    start = (today - timedelta(days=days)).isoformat()
    end = today.isoformat()

    by_day = client.reports().query(
        ids=MINE, startDate=start, endDate=end, metrics="views", dimensions="day",
    ).execute()
    by_country = client.reports().query(
        ids=MINE, startDate=start, endDate=end, metrics="views", dimensions="country",
        sort="-views", maxResults=10,
    ).execute()

    return {
        "by_day": by_day.get("rows", []),
        "by_country": by_country.get("rows", []),
    }
