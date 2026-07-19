from __future__ import annotations

import re
import sys
from pathlib import Path

import click
from rich.console import Console

from . import generate_text, generate_thumbnail, research, youtube_data
from .config import MissingConfig, get_settings
from .monetization import build_report, format_report_markdown

console = Console()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


@click.group()
def main():
    """ytcopilot — YouTube monetization diagnosis and content-planning copilot."""


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
@click.argument("topic")
@click.option("--niche", required=True)
@click.option("--length", "length_minutes", default=10, type=int, help="Target length in minutes.")
@click.option("--out-dir", type=click.Path(path_type=Path), default=Path("output"))
def plan(topic: str, niche: str, length_minutes: int, out_dir: Path):
    """Full pipeline for one video: script, chapters, titles, description, thumbnail brief+image."""
    settings = get_settings()
    slug = _slug(topic)
    video_dir = out_dir / slug
    video_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold]1/5[/] Writing script...")
    script = generate_text.generate_script(settings, topic, niche, length_minutes)
    (video_dir / "script.md").write_text(script)

    console.print("[bold]2/5[/] Building chapters...")
    chapters = generate_text.generate_chapters(settings, script, length_minutes)
    (video_dir / "chapters.json").write_text(_json_pretty(chapters))

    console.print("[bold]3/5[/] Generating title options...")
    titles = generate_text.generate_titles(settings, topic, niche, script_excerpt=script)
    (video_dir / "titles.md").write_text("\n".join(f"- {t}" for t in titles))
    chosen_title = titles[0]

    console.print("[bold]4/5[/] Writing description...")
    description = generate_text.generate_description(settings, topic, niche, chapters, script_excerpt=script)
    (video_dir / "description.md").write_text(description)

    console.print("[bold]5/5[/] Designing thumbnail...")
    brief = generate_thumbnail.generate_brief(settings, topic, niche, chosen_title)
    (video_dir / "thumbnail_brief.md").write_text(generate_thumbnail.format_brief_markdown(brief))
    try:
        settings.require_gemini_key()
        image_path = generate_thumbnail.render_thumbnail_image(settings, brief, video_dir / "thumbnail.png")
        console.print(f"  Thumbnail image saved to {image_path}")
    except MissingConfig as e:
        console.print(f"  [yellow]Skipped image render:[/] {e}")

    console.print(f"\n[green]Done.[/] All assets in {video_dir}/")
    console.print(f"Top title pick: [bold]{chosen_title}[/] (see titles.md for all options)")


@main.command()
@click.argument("topic")
@click.option("--niche", required=True)
@click.option("--title", required=True)
@click.option("--brief-only", is_flag=True, help="Skip image rendering even if GEMINI_API_KEY is set.")
@click.option("--out", type=click.Path(path_type=Path), default=Path("thumbnail.png"))
def thumbnail(topic: str, niche: str, title: str, brief_only: bool, out: Path):
    """Generate a standalone thumbnail brief (+ image, unless --brief-only) for one video."""
    settings = get_settings()
    brief = generate_thumbnail.generate_brief(settings, topic, niche, title)
    console.print(generate_thumbnail.format_brief_markdown(brief))
    if not brief_only:
        try:
            path = generate_thumbnail.render_thumbnail_image(settings, brief, out)
            console.print(f"\n[green]Image saved to {path}[/]")
        except MissingConfig as e:
            console.print(f"\n[yellow]{e}[/]")


def _json_pretty(obj) -> str:
    import json
    return json.dumps(obj, indent=2)


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
