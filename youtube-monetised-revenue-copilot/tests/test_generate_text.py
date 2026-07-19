from ytcopilot.generate_text import _safe_json_list


def test_safe_json_list_extracts_array_from_surrounding_text():
    raw = 'Sure, here you go:\n["Title One", "Title Two", "Title Three"]\nHope that helps!'
    assert _safe_json_list(raw) == ["Title One", "Title Two", "Title Three"]


def test_safe_json_list_raises_on_no_array():
    try:
        _safe_json_list("no array here")
        assert False, "expected ValueError"
    except ValueError:
        pass
