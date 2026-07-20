"""Text-to-video shot-list generation for long-form videos.

Long-form video *rendering* is deliberately not automated end-to-end: the
channel owner's own research into Google AI Pro's Flow quota (1,000 AI
credits/month, ~100 Veo Fast clips at 10 credits each) shows it's tight but
workable for one long-form video a month if spent manually and reviewed shot
by shot — whereas per-second paid API generation for a full 8-10 minute
video runs several times the channel's entire monthly video-gen budget. This
module produces the shot list only; rendering and stitching stay a manual,
reviewed step against whatever quota the owner has left that month.
"""

from __future__ import annotations

import json
import math

from google import genai
from google.genai import types

from . import channel_profile as profile
from .config import Settings

DEFAULT_CLIP_SECONDS = 8  # matches Veo Fast's clip length in Google Flow


def _client(settings: Settings) -> genai.Client:
    return genai.Client(api_key=settings.require_gemini_key())


def shot_count(length_minutes: float, clip_seconds: int = DEFAULT_CLIP_SECONDS) -> int:
    return math.ceil((length_minutes * 60) / clip_seconds)


def generate_shot_list(
    settings: Settings,
    script: str,
    chapters: list[dict],
    length_minutes: float,
    clip_seconds: int = DEFAULT_CLIP_SECONDS,
) -> list[dict]:
    clip_count = shot_count(length_minutes, clip_seconds)
    chapters_block = "\n".join(f"{c['timestamp']} {c['label']}" for c in chapters)

    prompt = f"""Break this finished YouTube script into exactly {clip_count} sequential \
text-to-video shots of {clip_seconds} seconds each, covering the full runtime in order \
(shot 1 = 0:00-0:{clip_seconds:02d}, shot 2 continues from there, and so on to the end).

Script:
{script}

Chapter map, for context on where each part of the script sits:
{chapters_block}

Visual style — every shot must follow this exactly, it's the channel's established look:
{profile.VIDEO_VISUAL_STYLE}

For each shot, write a complete, self-contained text-to-video prompt (portable to Veo, Sora, \
Kling, or any similar tool) describing ONLY what's on screen during that {clip_seconds}-second \
window — matched to what the narration is saying at that point in the script, supporting the \
idea visually rather than illustrating it literally word-for-word (e.g. a section about \
compounding interest could show a slow push-in on a rain-streaked office window at dusk, not a \
literal graph). Vary the composition/subject shot-to-shot so it doesn't read as the same clip \
repeated.

Return ONLY a JSON array of exactly {clip_count} objects, in order, each with these exact keys:
{{"index": 1, "start": "0:00", "end": "0:{clip_seconds:02d}", "chapter": "closest chapter label", \
"prompt": "the complete text-to-video prompt, including duration/aspect ratio (16:9) and style \
notes, ready to paste directly into a generator"}}"""

    client = _client(settings)
    resp = client.models.generate_content(
        model=settings.gemini_text_model,
        contents=prompt,
        config=types.GenerateContentConfig(max_output_tokens=8192),
    )
    raw = resp.text.strip()
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return a JSON array:\n{raw}")
    return json.loads(raw[start:end + 1])


def format_shot_list_markdown(shots: list[dict], clip_seconds: int = DEFAULT_CLIP_SECONDS) -> str:
    quota_note = (
        f"**{len(shots)} clips needed at {clip_seconds}s each.** Google AI Pro's Flow quota "
        "(Veo Fast, ~100 clips/month) is the intended source for these — check this total "
        "against however much of that quota you have left before generating, since re-rolls "
        "for bad takes eat into the same budget. Render manually, review each clip, then stitch "
        "in order.\n\n---\n\n"
    )
    body = "\n\n".join(
        f"### Shot {s['index']} ({s['start']}-{s['end']}) — {s.get('chapter', '')}\n"
        f"```\n{s['prompt']}\n```"
        for s in shots
    )
    return quota_note + body
