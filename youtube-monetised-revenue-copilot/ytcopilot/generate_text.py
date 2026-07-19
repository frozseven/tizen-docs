"""Script / title / description / chapter generation via the Gemini API.

Every prompt here bakes in two hard constraints on purpose:
1. Grounded in how YouTube's ranking and monetization systems actually work
   (retention-driven, not upload-volume-driven) rather than "growth hack"
   folklore — and, specifically, in the decoded formula in channel_profile.py,
   which the channel owner built from real competitor titles/views/subscriber
   data rather than generic advice.
2. Titles/thumbnails must accurately represent the video. YouTube's
   clickbait / misleading-metadata policy (support.google.com/youtube/answer/2801973)
   can suppress reach or strike a channel for titles that promise something
   the video doesn't deliver — so "honest but high-curiosity" is enforced in
   the prompt, not left to chance.
"""

from __future__ import annotations

import json

from google import genai
from google.genai import types

from . import channel_profile as profile
from .config import Settings

SYSTEM_PROMPT = f"""You are the scriptwriter for {profile.CHANNEL_NAME}. Hard rules, no exceptions:
- Never suggest engagement-bait phrasing (e.g. fake urgency about "the algorithm", \
begging/manipulative subscribe requests, "you won't believe" style false promises).
- Titles and thumbnail text must accurately represent what the video actually delivers. \
High curiosity is good; misrepresentation is not — YouTube's misleading-metadata policy \
can suppress or strike channels for it, which directly works against monetization.
- Optimize for retention (average view duration/percentage), because YPP eligibility and \
YouTube's own ranking system are both driven by watch time, not just clicks.
- Channel positioning: {profile.POSITIONING}
- Brand stance: "{profile.BRAND_LINE}" — this is a real editorial position, not a slogan to \
paste in. Nothing you write should read like a "guru" pitch, a fake-urgency ad, or a \
get-rich-quick claim, even implicitly.
- Target viewer: {profile.TARGET_AUDIENCE}
"""


def _client(settings: Settings) -> genai.Client:
    return genai.Client(api_key=settings.require_gemini_key())


def _generate(settings: Settings, user_prompt: str, max_tokens: int = 4096) -> str:
    client = _client(settings)
    resp = client.models.generate_content(
        model=settings.gemini_text_model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            max_output_tokens=max_tokens,
        ),
    )
    return resp.text


def generate_script(settings: Settings, topic: str, length_minutes: int, niche: str = "") -> str:
    sections = profile.script_sections(length_minutes)
    section_lines = "\n".join(
        f"- [{s['name'].upper()} {s['start']}-{s['end']}] {s['description']}"
        for s in sections
    )
    hook_lines = "\n".join(f"- {window}: {beat}" for window, beat in profile.HOOK_STRUCTURE)

    prompt = f"""Write a full YouTube video script.

Topic: {topic}
{"Niche/topic cluster: " + niche if niche else ""}
Target length: ~{length_minutes} minutes spoken (~{length_minutes * 150} words at ~150wpm)

Use this exact six-part structure, scaled to the runtime above. Mark each section inline as \
"[SECTION: <NAME> <start>-<end>]" using precisely these timestamps, so they can be lifted \
directly into chapters later:
{section_lines}

The OPEN section follows this exact four-beat hook structure — this is measured, not a \
guess: a same-channel, same-format video hit 950,200 views with a title/hook that named the \
viewer's feeling directly, versus 34,900 views for one that assumed a term the viewer didn't \
already know. Land the open on landing the feeling, not the term:
{hook_lines}

Pacing: {profile.PACING_RULES}

Call to action: {profile.CTA_RULE}

Other requirements:
- No stage directions, no "[music]" or "[visual: ...]" cues — narration text only.
- No filler opener ("Hey guys, welcome back") — start directly on the hook.
- One clean narration block per section, short natural sentences.

Output just the script text with the [SECTION: ...] markers inline."""
    return _generate(settings, prompt, max_tokens=8192)


def generate_titles(settings: Settings, topic: str, script_excerpt: str = "", n: int = 8, niche: str = "") -> list[str]:
    patterns_block = "\n".join(f"- {p['name']}: e.g. \"{p['example']}\"" for p in profile.TITLE_PATTERNS)
    prompt = f"""Generate {n} YouTube title options for this video.

Topic: {topic}
{"Niche/topic cluster: " + niche if niche else ""}
{"Script excerpt for grounding (titles must accurately reflect this content): " + script_excerpt[:1500] if script_excerpt else ""}

Draw from these measured title patterns — cover as many distinct patterns as you have options \
for, don't repeat the same one twice if you can avoid it:
{patterns_block}

Hard rule: {profile.TITLE_RULE}

Other constraints:
- Under 60 characters where possible (avoids truncation on mobile).
- Must be 100% honest about what the video delivers — no bait.

Return ONLY a JSON array of {n} strings, nothing else."""
    raw = _generate(settings, prompt, max_tokens=1024)
    return _safe_json_list(raw)


def generate_description(settings: Settings, topic: str, chapters: list[dict], script_excerpt: str = "", niche: str = "") -> str:
    chapters_block = "\n".join(f"{c['timestamp']} {c['label']}" for c in chapters)
    prompt = f"""Write a YouTube video description for this video.

Topic: {topic}
{"Niche/topic cluster: " + niche if niche else ""}
{"Script excerpt for grounding: " + script_excerpt[:1500] if script_excerpt else ""}

Requirements:
- First 2-3 lines (before the "show more" fold, ~125 chars) must hook AND include the primary \
keyword naturally — this is what shows in search results.
- Follow with 2-4 short paragraphs expanding on the value, naturally including relevant \
secondary keywords for search (no keyword stuffing).
- Include this exact chapters block verbatim, unmodified, at the point you'd naturally place it:
{chapters_block}
- Include this exact line verbatim, on its own, near the end: "{profile.BRAND_LINE}"
- End with a short, honest CTA (subscribe/next video) — no manipulative language.
- Add 3-5 relevant hashtags on the final line.
- Do NOT invent links, sponsors, or affiliate disclosures that weren't provided.

Output just the description text."""
    return _generate(settings, prompt, max_tokens=1024)


def generate_chapters(settings: Settings, script_text: str, length_minutes: int) -> list[dict]:
    sections = profile.script_sections(length_minutes)
    timestamps_block = "\n".join(f"- {s['name'].upper()}: starts at {s['start']}" for s in sections)
    prompt = f"""This script is marked with [SECTION: <NAME> <start>-<end>] breakpoints.

Script:
{script_text}

The section start timestamps are fixed — do not change them:
{timestamps_block}

Write a short, specific, non-generic chapter label for each section based on what that section \
actually covers in the script (e.g. "The 37% bracket nobody explains" rather than "Mechanism"). \
The first chapter MUST be 0:00.

Return ONLY a JSON array of objects like {{"timestamp": "0:00", "label": "..."}}, one per \
section, in order, nothing else."""
    raw = _generate(settings, prompt, max_tokens=1024)
    return _safe_json_objects(raw)


def _safe_json_list(raw: str) -> list[str]:
    raw = raw.strip()
    start, end = raw.find("["), raw.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return a JSON array:\n{raw}")
    return json.loads(raw[start:end + 1])


def _safe_json_objects(raw: str) -> list[dict]:
    return _safe_json_list(raw)  # same shape, list of JSON-decodable items
