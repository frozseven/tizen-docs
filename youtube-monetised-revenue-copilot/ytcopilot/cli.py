from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from . import channel_profile as profile
from . import content_authenticity, generate_thumbnail, pipeline, research, youtube_data
from .config import MissingConfig, get_settings
from .monetization import build_report, format_report_markdown

console = Console()


@click.group()
def main():
    """ytcopilot — YouTube monetization diagnosis and content-planning copilot for The Wealth Sheikh."""


@main.command()
def auth():
    """Run the one-time OAuth flow for YouTube Analytics (private data)."""
    from .oauth import get_credentials
    settings = get_settings()
    get_credentials(settings)
    console.print("[green]Authenticated.[/] Token saved for future runs.")


@main.command()
@click.argument("channel")
@click.option("--use-analytics", is_flag=True, help="Pull real watch-hour/Shorts-view data (requires `ytcopilot auth`).")
@click.option("--out", type=click.Path(path_type=Path), default=None, help="Write the report to this file as well as stdout.")
def diagnose(channel: str, use_analytics: bool, out: Path | None):
    """Diagnose monetization eligibility for CHANNEL (handle, URL, or channel ID)."""
    settings = get_settings()
    stats = youtube_data.get_channel_stats(settings, channel)

    watch = None
    if use_analytics:
        from . import youtube_analytics
        watch = youtube_analytics.get_watch_hour_summary(settings)

    report = build_report(stats, watch)
    md = format_report_markdown(report)
    console.print(md)
    if out:
        out.write_text(md)
        console.print(f"\n[dim]Saved to {out}[/]")


@click.command("research")
@click.argument("niche")
@click.option("--region", default="US")
def research_cmd(niche: str, region: str):
    """Find topic ideas and current trending videos for NICHE."""
    settings = get_settings()
    console.print(f"[bold]Top recent videos matching '{niche}' ({region}):[/]")
    for idea in research.suggest_topics(settings, niche, region=region):
        console.print(f"  - {idea.title}  [dim]({idea.channel_title}, {idea.published_at[:10]})[/]")

    console.print(f"\n[bold]Currently trending in this category ({region}):[/]")
    for v in research.trending_snapshot(settings, niche, region=region):
        console.print(f"  - {v['title']}  [dim]{v['view_count']:,} views — {v['channel_title']}[/]")


main.add_command(research_cmd)


@main.command()
@click.argument("niche")
@click.option("--use-analytics", is_flag=True)
def schedule(niche: str, use_analytics: bool):
    """Recommend posting days/times for NICHE targeting a US audience."""
    settings = get_settings()
    rec = research.recommend_posting_schedule(settings, niche, use_analytics)
    console.print(f"[bold]Source:[/] {rec['source']}")
    console.print(f"[dim]{rec['note']}[/]\n")
    if rec["source"] == "analytics":
        console.print("[bold]Your top days by views:[/] " + ", ".join(rec["top_days_by_views"]))
        console.print("[bold]Your top countries by views:[/] " + ", ".join(rec["top_countries_by_views"]))
        console.print("\n[bold]Suggested hour windows (benchmark, layer onto your top days):[/]")
        for w in rec["suggested_hour_windows"]:
            console.print(f"  - {w}")
    else:
        console.print("[bold]Suggested windows:[/]")
        for w in rec["windows"]:
            console.print(f"  - {w}")


@main.command()
@click.option("--months", default=3, type=int, help="Spread window in months.")
def rollout(months: int):
    """Suggest a gradual, week-by-week rollout schedule across the channel's niche clusters."""
    plan = research.rollout_plan(months=months)
    console.print(research.format_rollout_markdown(plan))


@main.command()
def ideas():
    """List the channel's decoded-formula seed video ideas."""
    console.print("[bold]Seed video ideas (from the decoded title/hook formula):[/]\n")
    for i, idea in enumerate(profile.SEED_VIDEO_IDEAS, 1):
        status = "[green]produced[/]" if idea["status"] == "produced" else "[yellow]idea[/]"
        console.print(f"{i}. {idea['title']}")
        console.print(f"   pattern: {idea['pattern']}  ·  {status}")


@main.command()
@click.option("--uploads-per-day", default=1.0, type=float)
@click.option("--ai-script-percent", default=90, type=int)
@click.option("--human-edit-pass/--no-human-edit-pass", default=True)
@click.option("--disclosure-on/--disclosure-off", default=True)
@click.option("--template-rotation-count", default=1, type=int, help="Distinct visual/script formats currently in rotation.")
@click.option("--new-niches-this-month", default=0, type=int)
@click.option("--human-pov-stated/--no-human-pov-stated", default=True)
def authenticity(
    uploads_per_day: float,
    ai_script_percent: int,
    human_edit_pass: bool,
    disclosure_on: bool,
    template_rotation_count: int,
    new_niches_this_month: int,
    human_pov_stated: bool,
):
    """Check current practices against the January-2026 'inauthentic content' termination-risk pattern."""
    flags = content_authenticity.assess_authenticity_risk(
        uploads_per_day=uploads_per_day,
        ai_script_percent=ai_script_percent,
        human_edit_pass=human_edit_pass,
        disclosure_on=disclosure_on,
        template_rotation_count=template_rotation_count,
        new_niches_this_month=new_niches_this_month,
        human_pov_stated=human_pov_stated,
    )
    console.print(content_authenticity.format_flags_markdown(flags))


@main.command()
@click.argument("topic")
@click.option("--niche", default="", help="Niche/topic cluster this video belongs to (optional context).")
@click.option("--length", "length_minutes", default=10, type=int, help="Target length in minutes.")
@click.option("--out-dir", type=click.Path(path_type=Path), default=Path("output"))
def plan(topic: str, niche: str, length_minutes: int, out_dir: Path):
    """Full pipeline for one video: script, chapters, titles, description, thumbnail brief+image."""
    settings = get_settings()

    def on_progress(index: int, name: str, status: str) -> None:
        if status == "active":
            console.print(f"[bold]{index + 1}/{len(pipeline.STEP_NAMES)}[/] {name}...")

    result = pipeline.run_plan_pipeline(settings, topic, niche, length_minutes, out_dir, on_progress=on_progress)

    if result["thumbnail_image_path"]:
        console.print(f"  Thumbnail image saved to {result['thumbnail_image_path']}")
    elif result["thumbnail_error"]:
        console.print(f"  [yellow]Skipped image render:[/] {result['thumbnail_error']}")

    console.print(f"\n[green]Done.[/] All assets in {result['video_dir']}/")
    console.print(f"Top title pick: [bold]{result['chosen_title']}[/] (see titles.md for all options)")
    console.print(f"Video-generation shot list: {len(result['shot_list'])} clips — see video_prompts.md "
                   "to render manually against your Google AI Pro Flow quota.")
    console.print("[yellow]Do the human edit pass before uploading — see the note at the end of script.md.[/]")


@main.command()
@click.argument("topic")
@click.option("--niche", default="", help="Niche/topic cluster this video belongs to (optional context).")
@click.option("--title", required=True)
@click.option("--brief-only", is_flag=True, help="Skip image rendering even if GEMINI_API_KEY is set.")
@click.option("--out", type=click.Path(path_type=Path), default=Path("thumbnail.png"))
@click.option("--out-dir", type=click.Path(path_type=Path), default=Path("output"), help="Where to look for recent thumbnails to avoid repeating.")
def thumbnail(topic: str, niche: str, title: str, brief_only: bool, out: Path, out_dir: Path):
    """Generate a standalone thumbnail brief (+ image, unless --brief-only) for one video."""
    settings = get_settings()
    recent_styles = pipeline.recent_thumbnail_styles(out_dir)
    brief = generate_thumbnail.generate_brief(settings, topic, title, niche=niche, recent_styles=recent_styles)
    console.print(generate_thumbnail.format_brief_markdown(brief))
    if not brief_only:
        try:
            path = generate_thumbnail.render_thumbnail_image(settings, brief, out)
            console.print(f"\n[green]Image saved to {path}[/]")
        except MissingConfig as e:
            console.print(f"\n[yellow]{e}[/]")


def _entrypoint():
    try:
        main()
    except MissingConfig as e:
        console.print(f"[red]Config error:[/] {e}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001 - top-level CLI error boundary
        console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


if __name__ == "__main__":
    _entrypoint()
