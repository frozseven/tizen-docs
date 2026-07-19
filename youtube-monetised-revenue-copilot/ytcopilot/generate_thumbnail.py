"""Thumbnail generation: Claude writes a design brief grounded in what
actually drives CTR without crossing into misleading territory, then Gemini
(Nano Banana / Imagen) renders it to a real PNG.

Design principles baked into the prompt (all well-documented, non-bait CTR
drivers): a single clear focal point, high subject/background contrast, a
legible 2-4 word text overlay that adds information the title doesn't
already say, and an accurate representation of the video's actual content —
misleading thumbnails are a documented cause of YouTube reach suppression
and channel strikes, i.e. they work against monetization, not for it.

One more constraint comes from the channel owner's own research: identical
templates repeated across every upload ("template sameness") was flagged as
the single biggest risk marker in a wave of January 2026 channel
terminations for "inauthentic content" (see content_authenticity.py). The
reference style in channel_profile.py is a real, working starting point —
not a fixed template to reuse verbatim on every video.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from . import channel_profile as profile
from .config import Settings

BRIEF_SYSTEM_PROMPT = """You are a YouTube thumbnail designer. Rules:
- The thumbnail must accurately represent the video's actual content. High curiosity/emotion is \
encouraged; fabricating a scene, object, or claim that isn't in the video is not allowed.
- One clear focal subject, uncluttered composition — thumbnails are judged at 120x67px in a \
mobile feed, so anything that isn't readable at that size should be cut.
- Text overlay: 2-4 words max, must ADD information the title doesn't already convey (numbers, \
a contrast, a specific stake), never just repeat the title.
- Strong subject/background contrast and a limited, deliberate color palette (2-3 colors) so it \
pops against a busy feed of other thumbnails.
"""


@dataclass
class ThumbnailBrief:
    composition: str
    focal_subject: str
    expression_or_mood: str
    text_overlay: str
    color_palette: str
    contrast_notes: str
    image_prompt: str


def _client(settings: Settings) -> Anthropic:
    return Anthropic(api_key=settings.require_anthropic_key())


def generate_brief(
    settings: Settings,
    topic: str,
    title: str,
    niche: str = "",
    recent_styles: list[str] | None = None,
) -> ThumbnailBrief:
    client = _client(settings)
    recent_styles = recent_styles or []
    avoid_block = (
        "Recent thumbnails already used these compositions/palettes — do not repeat them, "
        "pick a genuinely different layout or color treatment this time:\n"
        + "\n".join(f"- {s}" for s in recent_styles)
        if recent_styles
        else "No prior thumbnails recorded yet — you may use the reference style below as a "
        "starting point for this first one."
    )
    prompt = f"""Design a YouTube thumbnail for this video.

{"Niche/topic cluster: " + niche if niche else ""}
Video title: {title}
Topic/what the video actually covers: {topic}

Reference style that has worked for this channel before (a real starting point, not a template \
to copy on every video — see note above about template sameness):
{profile.THUMBNAIL_STYLE_REFERENCE}

{avoid_block}

Return ONLY a JSON object with these exact keys:
{{
  "composition": "layout description",
  "focal_subject": "the single main visual subject",
  "expression_or_mood": "facial expression / mood if a person is shown, or visual tone otherwise",
  "text_overlay": "2-4 words max",
  "color_palette": "2-3 colors and where each is used",
  "contrast_notes": "how the subject is separated from the background",
  "image_prompt": "a complete, self-contained text-to-image prompt combining all of the above \
into one paragraph, written for an image generation model, including the exact text_overlay \
string as rendered text in the image, 16:9 aspect ratio, photorealistic or bold-illustration \
style as appropriate for this channel"
}}"""
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1024,
        system=BRIEF_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text").strip()
    start, end = raw.find("{"), raw.rfind("}")
    data = json.loads(raw[start:end + 1])
    return ThumbnailBrief(**data)


def render_thumbnail_image(settings: Settings, brief: ThumbnailBrief, output_path: Path) -> Path:
    from google import genai

    client = genai.Client(api_key=settings.require_gemini_key())
    response = client.models.generate_content(
        model=settings.gemini_image_model,
        contents=[brief.image_prompt],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for candidate in response.candidates:
        for part in candidate.content.parts:
            if getattr(part, "inline_data", None) is not None:
                output_path.write_bytes(part.inline_data.data)
                return output_path

    raise RuntimeError(
        "Gemini did not return image data. Response text (if any): "
        + "".join(getattr(p, "text", "") or "" for c in response.candidates for p in c.content.parts)
    )


def format_brief_markdown(brief: ThumbnailBrief) -> str:
    return (
        f"**Composition:** {brief.composition}\n\n"
        f"**Focal subject:** {brief.focal_subject}\n\n"
        f"**Expression/mood:** {brief.expression_or_mood}\n\n"
        f"**Text overlay:** {brief.text_overlay}\n\n"
        f"**Color palette:** {brief.color_palette}\n\n"
        f"**Contrast notes:** {brief.contrast_notes}\n\n"
        f"**Full image-gen prompt (portable to any tool):**\n```\n{brief.image_prompt}\n```\n"
    )
