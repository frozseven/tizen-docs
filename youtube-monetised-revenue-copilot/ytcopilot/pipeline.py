"""Shared script -> chapters -> titles -> description -> thumbnail pipeline.

Used by both the CLI `plan` command and the web dashboard's background job,
so the actual generation logic lives in exactly one place rather than being
duplicated between an interactive CLI and an HTTP handler.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from . import generate_text, generate_thumbnail
from .config import MissingConfig, Settings

STEP_NAMES = [
    "Writing script",
    "Building chapters",
    "Generating title options",
    "Writing description",
    "Designing thumbnail",
]

# (step_index, step_name, status) where status is "active" | "done"
ProgressCallback = Callable[[int, str, str], None]

HUMAN_PASS_REMINDER = (
    "\n\n---\n"
    "REMINDER before uploading (do not skip): do a real human edit pass on this script — "
    "cut lines that don't sound like a specific person, add one thing that's genuinely "
    "yours. Confirm the 'altered or synthetic content' disclosure toggle is on in Studio. "
    "Run the authenticity check against known termination-risk markers before publishing.\n"
)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def recent_thumbnail_styles(out_dir: Path, limit: int = 5) -> list[str]:
    """Pulls composition/palette lines out of previously generated thumbnail
    briefs so the next brief is told what to avoid repeating."""
    styles: list[str] = []
    if not out_dir.exists():
        return styles
    for brief_path in sorted(out_dir.glob("*/thumbnail_brief.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = brief_path.read_text()
        comp = next((l for l in text.splitlines() if l.startswith("**Composition:**")), "")
        palette = next((l for l in text.splitlines() if l.startswith("**Color palette:**")), "")
        if comp or palette:
            styles.append(f"{comp} {palette}".strip())
        if len(styles) >= limit:
            break
    return styles


def run_plan_pipeline(
    settings: Settings,
    topic: str,
    niche: str,
    length_minutes: int,
    out_dir: Path,
    on_progress: ProgressCallback | None = None,
) -> dict:
    def report(i: int, status: str) -> None:
        if on_progress:
            on_progress(i, STEP_NAMES[i], status)

    video_slug = slug(topic)
    video_dir = out_dir / video_slug
    video_dir.mkdir(parents=True, exist_ok=True)

    report(0, "active")
    script = generate_text.generate_script(settings, topic, length_minutes, niche=niche)
    script_with_reminder = script + HUMAN_PASS_REMINDER
    (video_dir / "script.md").write_text(script_with_reminder)
    report(0, "done")

    report(1, "active")
    chapters = generate_text.generate_chapters(settings, script, length_minutes)
    (video_dir / "chapters.json").write_text(json.dumps(chapters, indent=2))
    report(1, "done")

    report(2, "active")
    titles = generate_text.generate_titles(settings, topic, script_excerpt=script, niche=niche)
    (video_dir / "titles.md").write_text("\n".join(f"- {t}" for t in titles))
    chosen_title = titles[0]
    report(2, "done")

    report(3, "active")
    description = generate_text.generate_description(settings, topic, chapters, script_excerpt=script, niche=niche)
    (video_dir / "description.md").write_text(description)
    report(3, "done")

    report(4, "active")
    recent_styles = recent_thumbnail_styles(out_dir)
    brief = generate_thumbnail.generate_brief(settings, topic, chosen_title, niche=niche, recent_styles=recent_styles)
    (video_dir / "thumbnail_brief.md").write_text(generate_thumbnail.format_brief_markdown(brief))
    thumbnail_image_path: Path | None = None
    thumbnail_error: str | None = None
    try:
        settings.require_gemini_key()
        thumbnail_image_path = generate_thumbnail.render_thumbnail_image(settings, brief, video_dir / "thumbnail.png")
    except MissingConfig as e:
        thumbnail_error = str(e)
    report(4, "done")

    return {
        "video_dir": video_dir,
        "slug": video_slug,
        "script": script_with_reminder,
        "chapters": chapters,
        "titles": titles,
        "chosen_title": chosen_title,
        "description": description,
        "thumbnail_brief": brief,
        "thumbnail_image_path": thumbnail_image_path,
        "thumbnail_error": thumbnail_error,
    }
