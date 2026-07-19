from ytcopilot.monetization import build_report, format_report_markdown
from ytcopilot.youtube_data import ChannelStats
from ytcopilot.youtube_analytics import WatchHourSummary


def _stats(subs: int) -> ChannelStats:
    return ChannelStats(
        channel_id="UC_test_000000000000000",
        handle="@test",
        title="Test Channel",
        description="",
        country="US",
        subscriber_count=subs,
        subscriber_count_hidden=False,
        view_count=100_000,
        video_count=50,
        published_at="2020-01-01T00:00:00Z",
        uploads_playlist_id="UU_test",
    )


def test_below_threshold_flagged_not_met():
    report = build_report(_stats(500), watch=None)
    subs_gap = next(g for g in report.api_checked if g.criterion == "Subscribers")
    assert subs_gap.status == "not_met"
    assert "500" in subs_gap.detail


def test_at_threshold_met():
    report = build_report(_stats(1000), watch=None)
    subs_gap = next(g for g in report.api_checked if g.criterion == "Subscribers")
    assert subs_gap.status == "met"


def test_watch_hours_route_met():
    watch = WatchHourSummary(
        trailing_365d_watch_hours=5000.0,
        trailing_90d_shorts_views=0,
        trailing_365d_views=200_000,
    )
    report = build_report(_stats(2000), watch=watch)
    wt_gap = next(g for g in report.api_checked if g.criterion == "Watch-time route")
    assert wt_gap.status == "met"


def test_shorts_route_met_even_if_watch_hours_low():
    watch = WatchHourSummary(
        trailing_365d_watch_hours=100.0,
        trailing_90d_shorts_views=12_000_000,
        trailing_365d_views=200_000,
    )
    report = build_report(_stats(2000), watch=watch)
    wt_gap = next(g for g in report.api_checked if g.criterion == "Watch-time route")
    assert wt_gap.status == "met"


def test_neither_route_met():
    watch = WatchHourSummary(
        trailing_365d_watch_hours=100.0,
        trailing_90d_shorts_views=1000,
        trailing_365d_views=5000,
    )
    report = build_report(_stats(2000), watch=watch)
    wt_gap = next(g for g in report.api_checked if g.criterion == "Watch-time route")
    assert wt_gap.status == "not_met"


def test_no_analytics_watch_hours_goes_to_manual_check():
    report = build_report(_stats(2000), watch=None)
    assert any(
        "Watch-time route" in g.criterion for g in report.manual_check_required
    )
    assert not any(g.criterion == "Watch-time route" for g in report.api_checked)


def test_manual_checks_always_include_strikes_and_adsense():
    report = build_report(_stats(2000), watch=None)
    criteria = [g.criterion for g in report.manual_check_required]
    assert any("strikes" in c.lower() for c in criteria)
    assert any("adsense" in c.lower() for c in criteria)


def test_markdown_report_renders_without_error():
    report = build_report(_stats(500), watch=None)
    md = format_report_markdown(report)
    assert "Test Channel" in md
    assert "Subscribers" in md
