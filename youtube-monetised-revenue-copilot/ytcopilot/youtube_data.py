"""Thin wrapper over the public YouTube Data API v3 (API-key auth only).

Every field returned here is genuinely public — subscriber/view/video counts,
video metadata, search results, trending charts. Nothing about watch hours,
revenue, strikes, or AdSense status is available through this API; that data
is either private to the channel owner (see youtube_analytics.py) or not
exposed by any API at all (see monetization.py for what has to be checked
by hand in YouTube Studio).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from googleapiclient.discovery import build

from .config import Settings


@dataclass
class ChannelStats:
    channel_id: str
    handle: str | None
    title: str
    description: str
    country: str | None
    subscriber_count: int | None
    subscriber_count_hidden: bool
    view_count: int
    video_count: int
    published_at: str
    uploads_playlist_id: str


def _client(settings: Settings):
    return build("youtube", "v3", developerKey=settings.require_youtube_api_key())


def _resolve_channel_id(youtube, channel: str) -> str:
    """Accepts a raw channel ID (UC...), an @handle, or a full URL."""
    channel = channel.strip()
    for prefix in ("https://www.youtube.com/", "https://youtube.com/", "youtube.com/"):
        if channel.startswith(prefix):
            channel = channel[len(prefix):]
    channel = channel.split("?", 1)[0].strip("/")

    if channel.startswith("UC") and len(channel) == 24:
        return channel

    handle = channel if channel.startswith("@") else f"@{channel}"
    resp = youtube.channels().list(part="id", forHandle=handle).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"No YouTube channel found for handle '{handle}'.")
    return items[0]["id"]


def get_channel_stats(settings: Settings, channel: str) -> ChannelStats:
    youtube = _client(settings)
    channel_id = _resolve_channel_id(youtube, channel)

    resp = youtube.channels().list(
        part="snippet,statistics,contentDetails",
        id=channel_id,
    ).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"Channel '{channel}' resolved to id {channel_id} but has no data.")
    item = items[0]
    snippet = item["snippet"]
    stats = item["statistics"]

    return ChannelStats(
        channel_id=channel_id,
        handle=snippet.get("customUrl"),
        title=snippet["title"],
        description=snippet.get("description", ""),
        country=snippet.get("country"),
        subscriber_count=None if stats.get("hiddenSubscriberCount") else int(stats.get("subscriberCount", 0)),
        subscriber_count_hidden=bool(stats.get("hiddenSubscriberCount", False)),
        view_count=int(stats.get("viewCount", 0)),
        video_count=int(stats.get("videoCount", 0)),
        published_at=snippet["publishedAt"],
        uploads_playlist_id=item["contentDetails"]["relatedPlaylists"]["uploads"],
    )


def list_recent_uploads(settings: Settings, channel: str, max_results: int = 25) -> list[dict]:
    """Recent uploads with duration/view/like counts, newest first."""
    youtube = _client(settings)
    channel_id = _resolve_channel_id(youtube, channel)
    stats = get_channel_stats(settings, channel_id)

    videos: list[dict] = []
    page_token = None
    while len(videos) < max_results:
        resp = youtube.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=stats.uploads_playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=page_token,
        ).execute()
        video_ids = [i["contentDetails"]["videoId"] for i in resp.get("items", [])]
        if video_ids:
            details = youtube.videos().list(
                part="snippet,statistics,contentDetails", id=",".join(video_ids)
            ).execute()
            for v in details.get("items", []):
                videos.append({
                    "video_id": v["id"],
                    "title": v["snippet"]["title"],
                    "published_at": v["snippet"]["publishedAt"],
                    "duration": v["contentDetails"]["duration"],
                    "view_count": int(v["statistics"].get("viewCount", 0)),
                    "like_count": int(v["statistics"].get("likeCount", 0)),
                    "comment_count": int(v["statistics"].get("commentCount", 0)),
                })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return videos[:max_results]


def search_topics(settings: Settings, query: str, region_code: str = "US", max_results: int = 15) -> list[dict]:
    youtube = _client(settings)
    resp = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        order="viewCount",
        regionCode=region_code,
        maxResults=max_results,
        publishedAfter=_days_ago_iso(90),
    ).execute()
    return [
        {
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel_title": item["snippet"]["channelTitle"],
            "published_at": item["snippet"]["publishedAt"],
        }
        for item in resp.get("items", [])
    ]


def trending_videos(settings: Settings, category_id: str | None = None, region_code: str = "US", max_results: int = 25) -> list[dict]:
    youtube = _client(settings)
    kwargs = dict(
        part="snippet,statistics",
        chart="mostPopular",
        regionCode=region_code,
        maxResults=max_results,
    )
    if category_id:
        kwargs["videoCategoryId"] = category_id
    resp = youtube.videos().list(**kwargs).execute()
    return [
        {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "channel_title": item["snippet"]["channelTitle"],
            "category_id": item["snippet"].get("categoryId"),
            "view_count": int(item["statistics"].get("viewCount", 0)),
        }
        for item in resp.get("items", [])
    ]


def _days_ago_iso(days: int) -> str:
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
