"""Brand profile and decoded content formula for The Wealth Sheikh.

Everything below comes from the channel owner's own research against real
competitor titles, view counts, and subscriber counts (five-plus channels
compared, including a same-channel/same-format A/B: "The Salary Trap" at
950.2k views vs. "The Cantillon Effect" at 34.9k views — a 27x spread from
one title-writing rule alone). Title/packaging patterns are measured from
that data; hook and script-structure timing are the structure that data
points to, not independently verified — treat them as the current working
theory, not settled fact, and update this file as retention data comes in
from real uploads.

This is deliberately a plain, hand-editable module rather than something
generated per-run: the channel's positioning and formula should change
slowly and on purpose, not silently drift between videos.
"""

from __future__ import annotations

CHANNEL_NAME = "The Wealth Sheikh"
CHANNEL_HANDLE = "@The.Wealth.Sheikh"

BRAND_LINE = "No hype. No fake gurus. No get-rich-quick schemes."

POSITIONING = (
    "Build Wealth. Leverage AI. Grow Your Career. Create More Freedom — for "
    "ambitious professionals, entrepreneurs, creators, and future business "
    "owners."
)

TARGET_AUDIENCE = (
    "Someone who suspects they're doing something wrong but can't name it — "
    "already working hard, feeling the gap between effort and result."
)

# Weight controls how often ytcopilot should surface topics from each
# cluster (see research.rollout_plan). Heavier clusters pay better
# (measured RPM spread across source channels ran roughly $5-$60) and fit
# the channel's actual positioning more directly than the "escape the
# salary" cluster does.
NICHE_CLUSTERS = {
    "income_machine": {
        "weight": "heavy",
        "niches": ["AI", "Automation", "YouTube", "Monetization"],
        "frame": "build an income machine",
    },
    "compound_what_you_have": {
        "weight": "heavy",
        "niches": ["Investing", "Productivity"],
        "frame": "compound what you have",
    },
    "escape_the_salary": {
        "weight": "light",
        "niches": ["Careers", "Personal Branding", "Freelancing", "Entrepreneurship"],
        "frame": "escape the salary",
    },
}

# Measured title patterns, from real competitor titles/views.
TITLE_PATTERNS = [
    {
        "name": "parenthetical_closer",
        "example": "80 Years of Life Taught Me This One Hard Truth (Watch Before It's Too Late)",
    },
    {
        "name": "first_person_credential",
        "example": "I Copied a $20k/Month Faceless Psychology Channel",
    },
    {
        "name": "system_blame_frame",
        "example": "The Salary Trap — Why The System Keeps You Broke",
    },
    {
        "name": "naive_question",
        "example": "Why Every Country Is in Debt? And Who Do They Owe?",
    },
    {
        "name": "number_as_spectacle",
        "example": "$40 Million in 30 sec",
    },
]

TITLE_RULE = (
    "Never put a term in the title the viewer has to already understand. Name "
    "the feeling; explain the mechanism inside the video, not the title. "
    "(Measured on one same-channel, same-format pair: 'The Salary Trap' — "
    "950,200 views — vs. 'The Cantillon Effect' — 34,900 views. Same production, "
    "27x spread, from this rule alone.)"
)

HOOK_STRUCTURE = [
    ("0:00-0:03", "Restate the title's promise as a flat claim."),
    ("0:03-0:08", "Sharpen it into the viewer's own life."),
    ("0:08-0:12", "Name the villain — the system, the habit, the assumption."),
    ("0:12-0:15", "Promise the mechanism. Do not deliver it yet."),
]

# (section, share_of_total_runtime, what_goes_here). Shares sum to 1.0 and
# scale to any target length — see generate_text.script_sections().
SCRIPT_STRUCTURE = [
    ("open", 0.03, "The hook — see HOOK_STRUCTURE."),
    ("stakes", 0.12, "Why this matters to the viewer specifically, right now."),
    ("mechanism", 0.35, "How it actually works — the core explainer."),
    ("proof", 0.20, "Concrete numbers, example, or case that makes it real."),
    ("reframe", 0.15, "What to do differently, tied to the channel's stance."),
    ("close", 0.15, "One CTA tied to the content. No mid-roll ask."),
]

PACING_RULES = (
    "Short sentences, one idea each, nothing over ~20 words. Cut anything "
    "that doesn't sound like a specific, opinionated person talking, not a "
    "narrator reading an article."
)

CTA_RULE = (
    "One ask, placed at the end, tied to what the video just delivered. "
    "Never a mid-roll 'like and subscribe' — it breaks the mechanism/proof "
    "flow the retention structure depends on."
)

# Seed concepts already checked against the formula above. Idea 1 has
# already been produced once (still-image cut) — treat its real retention
# data, once you have it, as the benchmark the other three need to beat,
# not as a template to copy shot-for-shot.
SEED_VIDEO_IDEAS = [
    {
        "title": "Why Your Raise Never Makes You Richer (The Math Nobody Shows You)",
        "pattern": "system_blame_frame + parenthetical_closer",
        "status": "produced",
    },
    {
        "title": "Why Can't You Just Work Harder to Get Rich?",
        "pattern": "naive_question",
        "status": "idea",
    },
    {
        "title": "I Automated 90% of My Work With AI (Here's What Broke)",
        "pattern": "first_person_credential",
        "status": "idea",
    },
    {
        "title": "What $1,000 a Month Actually Becomes in 10 Years",
        "pattern": "number_as_spectacle",
        "status": "idea",
    },
]

# Reference point, not a fixed template — see generate_thumbnail.py for why
# reusing this identically every video is a documented risk, not a feature.
THUMBNAIL_STYLE_REFERENCE = (
    "Deep navy background. Bold warm-gold numerals/text as the dominant "
    "element. One silhouetted human figure (no visible face) as the only "
    "secondary element. Two colors total plus background. No clutter."
)

# Same faceless/navy-gold positioning as THUMBNAIL_STYLE_REFERENCE, extended
# to full-motion b-roll so generated video stays consistent with the
# channel's established (and deliberately faceless) visual brand.
VIDEO_VISUAL_STYLE = (
    "Cinematic, photorealistic b-roll. Deep navy/blue-black environments lit "
    "with warm gold accent light (windows, desk lamps, city lights at dusk). "
    "Slow, deliberate camera moves (push-in, slow pan, rack focus) — no "
    "shaky or frantic motion. Human figures, when present, are shown from "
    "behind, in silhouette, or with faces out of frame/in shadow — never a "
    "clear, identifiable face on screen. No on-screen text or captions "
    "(added in post)."
)


def title_patterns_used(pattern_field: str) -> list[dict]:
    """Resolves a SEED_VIDEO_IDEAS `pattern` string like
    "system_blame_frame + parenthetical_closer" into the matching
    TITLE_PATTERNS entries, so callers can show *why* a title follows a
    measured pattern (with the real example) — deliberately not a fabricated
    performance score, since no title pattern can actually predict view
    counts; see README's "What this is, and isn't."
    """
    by_name = {p["name"]: p for p in TITLE_PATTERNS}
    names = [n.strip() for n in pattern_field.split("+")]
    return [by_name[n] for n in names if n in by_name]


MIN_OPEN_SECONDS = 15.0  # HOOK_STRUCTURE's four beats need this regardless of total runtime


def script_sections(length_minutes: float) -> list[dict]:
    """SCRIPT_STRUCTURE's proportions scaled to a concrete runtime, as
    explicit MM:SS boundaries a script prompt (or a human editor) can target.

    The open/hook section is floored at MIN_OPEN_SECONDS: below ~8.3 minutes
    total, its raw 3% share falls under the 15 seconds HOOK_STRUCTURE's four
    beats need, which would silently squeeze the hook on any shorter video.
    The remaining sections split whatever runtime is left in their existing
    proportions, so this is a no-op for videos long enough that the 3% share
    already clears the floor on its own.
    """
    total_seconds = length_minutes * 60
    open_name, open_share, open_description = SCRIPT_STRUCTURE[0]
    rest = SCRIPT_STRUCTURE[1:]
    rest_weight_total = sum(share for _, share, _ in rest)

    open_seconds = max(MIN_OPEN_SECONDS, open_share * total_seconds)
    remaining_seconds = max(total_seconds - open_seconds, 0.0)

    sections = [{
        "name": open_name,
        "start": _format_mmss(0),
        "end": _format_mmss(open_seconds),
        "description": open_description,
    }]
    elapsed = open_seconds
    for name, share, description in rest:
        start = elapsed
        elapsed += remaining_seconds * (share / rest_weight_total)
        sections.append({
            "name": name,
            "start": _format_mmss(start),
            "end": _format_mmss(elapsed),
            "description": description,
        })
    return sections


def _format_mmss(seconds: float) -> str:
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes}:{secs:02d}"
