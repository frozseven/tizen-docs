"""YouTube Partner Program (YPP) eligibility checker.

Thresholds below are YouTube's actual published requirements (current as of
this tool's last update — YouTube can and does change program terms, so
cross-check https://support.google.com/youtube/answer/72851 if this has
aged). Some eligibility criteria are not exposed by any API and can only be
seen by the channel owner inside YouTube Studio; this module says so
explicitly for each one rather than guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .youtube_data import ChannelStats
from .youtube_analytics import WatchHourSummary

SUBSCRIBER_THRESHOLD = 1000
WATCH_HOURS_THRESHOLD = 4000
SHORTS_VIEWS_THRESHOLD = 10_000_000


@dataclass
class Gap:
    criterion: str
    status: str  # "met" | "not_met" | "unknown_manual_check"
    detail: str
    how_to_fix: str


@dataclass
class MonetizationReport:
    channel_title: str
    api_checked: list[Gap] = field(default_factory=list)
    manual_check_required: list[Gap] = field(default_factory=list)

    @property
    def api_checks_passed(self) -> bool:
        return all(g.status == "met" for g in self.api_checked)


def build_report(
    stats: ChannelStats,
    watch: WatchHourSummary | None,
) -> MonetizationReport:
    report = MonetizationReport(channel_title=stats.title)

    subs = stats.subscriber_count or 0
    if subs >= SUBSCRIBER_THRESHOLD:
        report.api_checked.append(Gap(
            "Subscribers", "met",
            f"{subs:,} subscribers (threshold: {SUBSCRIBER_THRESHOLD:,}).",
            "",
        ))
    else:
        needed = SUBSCRIBER_THRESHOLD - subs
        report.api_checked.append(Gap(
            "Subscribers", "not_met",
            f"{subs:,} subscribers, {needed:,} short of the {SUBSCRIBER_THRESHOLD:,} threshold.",
            "Subscribers come from consistent, findable uploads in one clear niche — "
            "see `ytcopilot research` for topic/keyword targeting and `ytcopilot schedule` "
            "for posting cadence/timing.",
        ))

    if watch is not None:
        wh = watch.trailing_365d_watch_hours
        sv = watch.trailing_90d_shorts_views
        meets_watch_route = wh >= WATCH_HOURS_THRESHOLD
        meets_shorts_route = sv >= SHORTS_VIEWS_THRESHOLD
        if meets_watch_route or meets_shorts_route:
            route = "watch-hours" if meets_watch_route else "Shorts-views"
            report.api_checked.append(Gap(
                "Watch-time route", "met",
                f"Qualifies via the {route} route "
                f"({wh:,.0f}h long-form watch time / 12mo, {sv:,} Shorts views / 90d).",
                "",
            ))
        else:
            report.api_checked.append(Gap(
                "Watch-time route", "not_met",
                f"{wh:,.0f}h of {WATCH_HOURS_THRESHOLD:,}h needed (trailing 12mo) via long-form, "
                f"OR {sv:,} of {SHORTS_VIEWS_THRESHOLD:,} Shorts views needed (trailing 90d). "
                "Neither route is met yet.",
                "Watch-hours scale with average view duration x views, not just views — "
                "retention (hook quality, pacing, avoiding mid-video drop-off) usually moves "
                "this faster than raw upload volume. Use `ytcopilot script` to structure "
                "scripts around a strong first-15-seconds hook and re-hooks every ~2 minutes.",
            ))
    else:
        report.manual_check_required.append(Gap(
            "Watch-time route (4,000h/12mo long-form OR 10M Shorts views/90d)",
            "unknown_manual_check",
            "This is private data — the public Data API cannot see it. "
            "Run `ytcopilot auth` then re-run with `--use-analytics` to pull it for real, "
            "or check YouTube Studio > Analytics > Advanced mode > Watch time.",
            "",
        ))

    for item, where in [
        ("No active Community Guidelines strikes",
         "YouTube Studio > Settings > Channel > Feature eligibility, or Content > Copyright."),
        ("2-Step Verification enabled on the linked Google Account",
         "myaccount.google.com/security > 2-Step Verification."),
        ("AdSense account created and linked",
         "YouTube Studio > Earn > Overview, or Settings > Monetization."),
        ("Channel located in a country where YPP is available",
         "YouTube Studio > Settings > Channel > Advanced settings shows your country; "
         "compare against https://support.google.com/youtube/answer/72851."),
        ("Content complies with monetization policies "
         "(advertiser-friendly guidelines, no repetitious/reused mass-produced content, "
         "no clickbait/misleading titles-thumbnails at scale)",
         "YouTube Studio > Content — check individual videos for yellow/limited-ads icons, "
         "and review https://support.google.com/youtube/answer/1311392 (advertiser-friendly) "
         "and https://support.google.com/youtube/answer/10072907 (reused content)."),
    ]:
        report.manual_check_required.append(Gap(
            item, "unknown_manual_check",
            "Not exposed by any YouTube API — only visible to the signed-in channel owner.",
            where,
        ))

    return report


def format_report_markdown(report: MonetizationReport) -> str:
    lines = [f"# Monetization Diagnosis — {report.channel_title}", ""]
    lines.append("## Checked against real channel data")
    for g in report.api_checked:
        icon = "✅" if g.status == "met" else "❌"
        lines.append(f"- {icon} **{g.criterion}** — {g.detail}")
        if g.how_to_fix:
            lines.append(f"  - *Fix:* {g.how_to_fix}")
    lines.append("")
    lines.append("## Requires a manual check (not visible to any API)")
    for g in report.manual_check_required:
        lines.append(f"- ⬜ **{g.criterion}**")
        lines.append(f"  - {g.detail}")
        if g.how_to_fix:
            lines.append(f"  - *Where:* {g.how_to_fix}")
    return "\n".join(lines)
