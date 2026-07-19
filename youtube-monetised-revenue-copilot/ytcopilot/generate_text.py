"""Script / title / description / chapter generation via the Anthropic API.

Every prompt here bakes in two hard constraints on purpose:
1. Grounded in how YouTube's ranking and monetization systems actually work
   (retention-driven, not upload-volume-driven) rather than "growth hack"
   folklore.
2. Titles/thumbnails must accurately represent the video. YouTube's
   clickbait / misleading-metadata policy (support.google.com/youtube/answer/2801973)
   can suppress reach or strike a channel for titles that promise something
   the video doesn't deliver — so "honest but high-curiosity" is enforced in
   the prompt, not left to chance.
"""

from __future__ import annotations

import json

from anthropic import Anthropic

from .config import Settings

SYSTEM_PROMPT = """You are a YouTube content strategist. Hard rules, no exceptions:
- Never suggest engagement-bait phrasing (e.g. fake urgency about "the algorithm", \
begging/manipulative subscribe requests, "you won't believe" style false promises).
- Titles and thumbnail text must accurately represent what the video actually delivers. \
High curiosity is good; misrepresentation is not — YouTube's misleading-metadata policy \
can suppress or strike channels for it, which directly works against monetization.
- Optimize for retention (average view duration/percentage), because YPP eligibility and \
YouTube's own ranking system are both driven by watch time, not just clicks.
- Write for a real human audience in the stated niche, not generic filler.
"""


def _client(settings: Settings) -> Anthropic:
    return Anthropic(api_key=settings.require_anthropic_key())


def _generate(settings: Settings, user_prompt: str, max_tokens: int = 4096) -> str:
    client = _client(settings)
    resp = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def generate_script(settings: Settings, topic: str, niche: str, length_minutes: int) -> str:
    prompt = f"""Write a full YouTube video script for a "{niche}" channel.

Topic: {topic}
Target length: ~{length_minutes} minutes spoken (~{length_minutes * 150} words at ~150wpm)

Structure requirements:
- 0:00-0:15 hook: state the specific payoff/stakes immediately, no throat-clearing intro, \
no channel-name preamble.
- A clear promise of what the viewer will know/be able to do by the end, stated in the hook.
- A re-hook (pattern interrupt / new open loop) roughly every 90-120 seconds to defend against \
mid-video drop-off — this is the single biggest lever on watch-hours toward monetization.
- Section breaks marked as "[SECTION: <short label>]" so they can be converted into chapter \
timestamps later.
- One natural, non-begging call-to-subscribe placed after the strongest value moment (not at \
the very start or as a generic outro tack-on).
- End on a specific next-step or a forward-reference to a follow-up video (retention/session \
signal), not a generic "thanks for watching."

Output just the script text with [SECTION: ...] markers inline."""
    return _generate(settings, prompt, max_tokens=8192)


def generate_titles(settings: Settings, topic: str, niche: str, script_excerpt: str = "", n: int = 8) -> list[str]:
    prompt = f"""Generate {n} YouTube title options for this "{niche}" video.

Topic: {topic}
{"Script excerpt for grounding (titles must accurately reflect this content): " + script_excerpt[:1500] if script_excerpt else ""}

Constraints:
- Under 60 characters where possible (avoids truncation on mobile).
- High curiosity/specificity (numbers, concrete outcomes, contrast) but must be 100% honest \
about what the video delivers — no bait.
- Vary the angle across the {n} options (e.g. curiosity gap, direct benefit, contrarian take, \
specific number/result, question).

Return ONLY a JSON array of {n} strings, nothing else."""
    raw = _generate(settings, prompt, max_tokens=1024)
    return _safe_json_list(raw)


def generate_description(settings: Settings, topic: str, niche: str, chapters: list[dict], script_excerpt: str = "") -> str:
    chapters_block = "\n".join(f"{c['timestamp']} {c['label']}" for c in chapters)
    prompt = f"""Write a YouTube video description for this "{niche}" video.

Topic: {topic}
{"Script excerpt for grounding: " + script_excerpt[:1500] if script_excerpt else ""}

Requirements:
- First 2-3 lines (before the "show more" fold, ~125 chars) must hook AND include the primary \
keyword naturally — this is what shows in search results.
- Follow with 2-4 short paragraphs expanding on the value, naturally including relevant \
secondary keywords for search (no keyword stuffing).
- Include this exact chapters block verbatim, unmodified, at the point you'd naturally place it:
{chapters_block}
- End with a short, honest CTA (subscribe/next video) — no manipulative language.
- Do NOT invent links, sponsors, or affiliate disclosures that weren't provided.

Output just the description text."""
    return _generate(settings, prompt, max_tokens=1024)


def generate_chapters(settings: Settings, script_text: str, length_minutes: int) -> list[dict]:
    prompt = f"""This script is marked with [SECTION: <label>] breakpoints and is meant to run \
about {length_minutes} minutes total.

Script:
{script_text}

Convert the [SECTION: ...] markers into YouTube chapter timestamps. Distribute timestamps \
proportionally across the {length_minutes}-minute runtime based on each section's approximate \
share of the script's word count. The first chapter MUST be 0:00. Format each timestamp as \
M:SS or H:MM:SS.

Return ONLY a JSON array of objects like {{"timestamp": "0:00", "label": "..."}}, nothing else."""
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
