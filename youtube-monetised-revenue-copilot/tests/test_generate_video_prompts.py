from ytcopilot.generate_video_prompts import format_shot_list_markdown, shot_count


def test_shot_count_rounds_up_to_a_whole_clip():
    # 10 minutes = 600s; 600/8 = 75.0 exactly.
    assert shot_count(10, clip_seconds=8) == 75
    # 9 minutes = 540s; 540/8 = 67.5 -> needs 68 clips to cover the tail.
    assert shot_count(9, clip_seconds=8) == 68


def test_shot_count_respects_custom_clip_length():
    assert shot_count(1, clip_seconds=6) == 10  # 60/6 exactly


def test_format_shot_list_markdown_includes_quota_note_and_every_shot():
    shots = [
        {"index": 1, "start": "0:00", "end": "0:08", "chapter": "Open", "prompt": "prompt one"},
        {"index": 2, "start": "0:08", "end": "0:16", "chapter": "Stakes", "prompt": "prompt two"},
    ]
    md = format_shot_list_markdown(shots, clip_seconds=8)
    assert "2 clips needed at 8s each" in md
    assert "Google AI Pro's Flow quota" in md
    assert "Shot 1 (0:00-0:08) — Open" in md
    assert "prompt one" in md
    assert "Shot 2 (0:08-0:16) — Stakes" in md
    assert "prompt two" in md
