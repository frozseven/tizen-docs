""""Inauthentic content" termination-risk checklist.

In January 2026 YouTube broadened its "repetitious content" policy into
"inauthentic content" and, under it, permanently terminated (not
demonetized — deleted) sixteen channels with a combined 4.7 billion views
and 35 million subscribers. The shared pattern across those channels:
faceless format, TTS/synthetic narration, templated scripts, multiple
uploads per day, and sudden topic pivots that read as an algorithm play.

This is directly relevant to any AI-generated, faceless channel — the risk
isn't hypothetical, and it's a termination risk, not a demonetization risk,
which is why it gets its own module instead of folding into monetization.py.
Reported protective factors: original value, a stated human point of view,
original research, unique editing — none of which any API can verify, so
this module scores the *inputs you control* rather than pretending to
detect the outcome.

None of this is an official YouTube API or published scoring system — it's
the channel owner's own risk model, built from that January 2026 pattern.
Treat "high" flags as "stop and think," not as a guaranteed strike.
"""

from __future__ import annotations

from dataclasses import dataclass

FARM_THRESHOLD_UPLOADS_PER_DAY = 10  # reported pattern in the terminated channels
CAUTION_UPLOADS_PER_DAY = 3


@dataclass
class RiskFlag:
    marker: str
    severity: str  # "ok" | "caution" | "high"
    detail: str
    mitigation: str


def assess_authenticity_risk(
    *,
    uploads_per_day: float,
    ai_script_percent: int,
    human_edit_pass: bool,
    disclosure_on: bool,
    template_rotation_count: int,
    new_niches_this_month: int,
    human_pov_stated: bool,
) -> list[RiskFlag]:
    flags: list[RiskFlag] = []

    if uploads_per_day >= FARM_THRESHOLD_UPLOADS_PER_DAY:
        flags.append(RiskFlag(
            "Upload frequency", "high",
            f"{uploads_per_day:g}/day matches the reported farm threshold "
            f"({FARM_THRESHOLD_UPLOADS_PER_DAY}+/day on an identical template) from the "
            "January 2026 terminations.",
            "Cut volume, or make each upload visibly less templated (different structure, "
            "visuals, or angle) before pushing more videos out.",
        ))
    elif uploads_per_day >= CAUTION_UPLOADS_PER_DAY:
        flags.append(RiskFlag(
            "Upload frequency", "caution",
            f"{uploads_per_day:g}/day is under the reported {FARM_THRESHOLD_UPLOADS_PER_DAY}/day "
            "farm threshold, but volume amplifies whatever retention signal you're already "
            "sending — good or bad.",
            "Fine if retention is healthy; if it isn't, fix retention before adding volume.",
        ))
    else:
        flags.append(RiskFlag(
            "Upload frequency", "ok",
            f"{uploads_per_day:g}/day, well under the reported farm threshold.", "",
        ))

    if ai_script_percent >= 90 and not human_edit_pass:
        flags.append(RiskFlag(
            "AI-generated script share", "high",
            f"~{ai_script_percent}% AI-written with no human edit pass — the exact profile "
            "flagged in the terminated channels.",
            "Do a real edit pass per script (not a skim): cut lines that don't sound like a "
            "specific person, add one thing that's genuinely yours.",
        ))
    elif ai_script_percent >= 90:
        flags.append(RiskFlag(
            "AI-generated script share", "caution",
            f"~{ai_script_percent}% AI-written, with a human edit pass in place.",
            "Keep the edit pass substantive, not cosmetic — it's the main thing distinguishing "
            "this from the terminated channels' pattern.",
        ))
    else:
        flags.append(RiskFlag(
            "AI-generated script share", "ok",
            f"~{ai_script_percent}% AI-written.", "",
        ))

    if not disclosure_on:
        flags.append(RiskFlag(
            "Altered/synthetic content disclosure", "high",
            "Disclosure toggle is off for AI-generated content.",
            "Turn it on in YouTube Studio for every upload that uses synthetic narration/visuals "
            "— it's free, it's required, and leaving it off is itself a policy violation "
            "independent of everything else on this list.",
        ))
    else:
        flags.append(RiskFlag(
            "Altered/synthetic content disclosure", "ok", "Disclosure toggle is on.", "",
        ))

    if template_rotation_count <= 1:
        flags.append(RiskFlag(
            "Template sameness", "high",
            "Only one visual/script template in rotation — the single biggest risk marker "
            "identified in this channel's own research into the terminated channels.",
            "Rotate at least 3-4 distinct formats (visual style, pacing, structure) across "
            "uploads so no two consecutive videos look interchangeable.",
        ))
    elif template_rotation_count == 2:
        flags.append(RiskFlag(
            "Template sameness", "caution",
            "Two templates in rotation — better than one, still narrow.",
            "Add at least one more distinct format if upload volume increases.",
        ))
    else:
        flags.append(RiskFlag(
            "Template sameness", "ok",
            f"{template_rotation_count} distinct templates in rotation.", "",
        ))

    if new_niches_this_month >= 5:
        flags.append(RiskFlag(
            "Topic pivot speed", "high",
            f"{new_niches_this_month} new niches introduced this month — reads as an "
            "algorithm-chasing pivot rather than a channel finding its footing.",
            "Slow down: roll new niches in gradually (see research.rollout_plan — this "
            "channel's own plan spreads ten niches over 2-3 months, ~1 new one every week or "
            "two) and keep a visible through-line connecting them.",
        ))
    elif new_niches_this_month >= 3:
        flags.append(RiskFlag(
            "Topic pivot speed", "caution",
            f"{new_niches_this_month} new niches introduced this month.",
            "Still gradual, but keep it there — don't compress the rollout further.",
        ))
    else:
        flags.append(RiskFlag(
            "Topic pivot speed", "ok",
            f"{new_niches_this_month} new niche(s) introduced this month.", "",
        ))

    if not human_pov_stated:
        flags.append(RiskFlag(
            "Stated human point of view", "caution",
            "No clearly stated editorial stance found.",
            "This is reportedly the strongest available defense, and it costs nothing: state "
            "the channel's actual position (e.g. an explicit anti-hype, anti-guru stance) "
            "somewhere visible — About page, video opens, description.",
        ))
    else:
        flags.append(RiskFlag(
            "Stated human point of view", "ok",
            "Channel has a clearly stated editorial stance.", "",
        ))

    return flags


def format_flags_markdown(flags: list[RiskFlag]) -> str:
    icons = {"ok": "✅", "caution": "⚠️", "high": "🛑"}
    lines = ["# Inauthentic-content risk check", ""]
    high = [f for f in flags if f.severity == "high"]
    if high:
        lines.append(f"**{len(high)} high-severity flag(s) — these match the pattern YouTube "
                      "terminated channels for in January 2026, not just demonetized them.**")
        lines.append("")
    for f in flags:
        lines.append(f"- {icons[f.severity]} **{f.marker}** — {f.detail}")
        if f.mitigation:
            lines.append(f"  - *Do this:* {f.mitigation}")
    return "\n".join(lines)
