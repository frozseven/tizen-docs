from ytcopilot.channel_profile import SCRIPT_STRUCTURE, script_sections


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
