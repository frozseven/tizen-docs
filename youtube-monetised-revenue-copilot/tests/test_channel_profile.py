from ytcopilot.channel_profile import (
    MIN_OPEN_SECONDS,
    SCRIPT_STRUCTURE,
    SEED_VIDEO_IDEAS,
    TITLE_PATTERNS,
    script_sections,
    title_patterns_used,
)


def test_script_structure_shares_sum_to_one():
    total = sum(share for _, share, _ in SCRIPT_STRUCTURE)
    assert abs(total - 1.0) < 1e-9


def test_script_sections_starts_at_zero_and_ends_at_runtime():
    sections = script_sections(10)
    assert sections[0]["start"] == "0:00"
    assert sections[-1]["end"] == "10:00"


def test_script_sections_covers_all_structure_entries_in_order():
    sections = script_sections(8)
    names = [s["name"] for s in sections]
    assert names == [name for name, _, _ in SCRIPT_STRUCTURE]


def test_script_sections_boundaries_are_contiguous():
    sections = script_sections(12)
    for prev, nxt in zip(sections, sections[1:]):
        assert prev["end"] == nxt["start"]


def test_short_video_open_section_floored_at_min_hook_length():
    # 5 minutes: raw 3% share (9s) would otherwise squeeze HOOK_STRUCTURE's 15s.
    sections = script_sections(5)
    assert sections[0]["start"] == "0:00"
    assert sections[0]["end"] == "0:15"
    assert sections[-1]["end"] == "5:00"


def test_long_video_open_section_unaffected_by_floor():
    # 10 minutes: 3% share is 18s, already above the 15s floor — no clamping.
    sections = script_sections(10)
    assert sections[0]["end"] == "0:18"


def test_script_sections_never_produce_negative_or_out_of_order_boundaries():
    for length in (1, 3, 5, 8, 10, 20):
        sections = script_sections(length)
        for s in sections:
            start_secs = _mmss_to_seconds(s["start"])
            end_secs = _mmss_to_seconds(s["end"])
            assert start_secs <= end_secs


def _mmss_to_seconds(mmss: str) -> int:
    minutes, seconds = mmss.split(":")
    return int(minutes) * 60 + int(seconds)


def test_title_patterns_used_resolves_single_pattern():
    result = title_patterns_used("naive_question")
    assert [p["name"] for p in result] == ["naive_question"]


def test_title_patterns_used_resolves_multiple_patterns_in_order():
    result = title_patterns_used("system_blame_frame + parenthetical_closer")
    assert [p["name"] for p in result] == ["system_blame_frame", "parenthetical_closer"]


def test_title_patterns_used_skips_unknown_pattern_names():
    result = title_patterns_used("naive_question + not_a_real_pattern")
    assert [p["name"] for p in result] == ["naive_question"]


def test_every_seed_idea_pattern_resolves_to_at_least_one_known_pattern():
    known_names = {p["name"] for p in TITLE_PATTERNS}
    for idea in SEED_VIDEO_IDEAS:
        resolved = title_patterns_used(idea["pattern"])
        assert resolved, f"idea {idea['title']!r} pattern {idea['pattern']!r} matched nothing"
        assert {p["name"] for p in resolved} <= known_names
