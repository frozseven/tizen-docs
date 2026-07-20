from unittest.mock import MagicMock

from ytcopilot.youtube_data import _resolve_channel_id


def test_resolve_channel_id_passthrough_for_raw_id():
    youtube = MagicMock()
    channel_id = _resolve_channel_id(youtube, "UCX6OQ3DkcsbYNE6H8uQQuVA")
    assert channel_id == "UCX6OQ3DkcsbYNE6H8uQQuVA"
    youtube.channels.assert_not_called()


def test_resolve_channel_id_strips_url_and_adds_at():
    youtube = MagicMock()
    youtube.channels.return_value.list.return_value.execute.return_value = {
        "items": [{"id": "UCabc"}]
    }
    channel_id = _resolve_channel_id(youtube, "https://www.youtube.com/@the.wealth.sheikh?si=abc")
    assert channel_id == "UCabc"
    _, kwargs = youtube.channels.return_value.list.call_args
    assert kwargs["forHandle"] == "@the.wealth.sheikh"


def test_resolve_channel_id_raises_when_not_found():
    youtube = MagicMock()
    youtube.channels.return_value.list.return_value.execute.return_value = {"items": []}
    try:
        _resolve_channel_id(youtube, "@doesnotexist")
        assert False, "expected ValueError"
    except ValueError:
        pass
