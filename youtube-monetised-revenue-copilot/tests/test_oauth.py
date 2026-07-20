import json

from ytcopilot import oauth
from ytcopilot.config import Settings


def test_has_saved_credentials_true_from_token_file(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text("{}")
    settings = Settings(oauth_token_path=token_path)
    assert oauth.has_saved_credentials(settings)


def test_has_saved_credentials_true_from_refresh_token_env_with_no_file(tmp_path):
    settings = Settings(
        oauth_token_path=tmp_path / "missing.json",
        youtube_oauth_refresh_token="refresh-abc",
    )
    assert oauth.has_saved_credentials(settings)


def test_has_saved_credentials_false_when_neither_present(tmp_path):
    settings = Settings(oauth_token_path=tmp_path / "missing.json")
    assert not oauth.has_saved_credentials(settings)


def test_get_credentials_bootstraps_from_refresh_token_when_file_missing(tmp_path, monkeypatch):
    token_path = tmp_path / "missing.json"
    settings = Settings(
        oauth_token_path=token_path,
        oauth_client_id="client-id",
        oauth_client_secret="client-secret",
        youtube_oauth_refresh_token="refresh-abc",
    )

    def fake_refresh(self, request):
        self.token = "fresh-access-token"

    monkeypatch.setattr("google.oauth2.credentials.Credentials.refresh", fake_refresh)

    creds = oauth.get_credentials(settings)

    assert creds.token == "fresh-access-token"
    assert creds.refresh_token == "refresh-abc"
    # Refreshed credentials get written back to disk so this process's
    # subsequent calls in the same run don't re-hit the network.
    assert token_path.exists()
    assert json.loads(token_path.read_text())["refresh_token"] == "refresh-abc"


def test_get_saved_refresh_token_reads_from_file(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(json.dumps({"refresh_token": "refresh-xyz"}))
    settings = Settings(oauth_token_path=token_path)
    assert oauth.get_saved_refresh_token(settings) == "refresh-xyz"


def test_get_saved_refresh_token_none_when_no_file(tmp_path):
    settings = Settings(oauth_token_path=tmp_path / "missing.json")
    assert oauth.get_saved_refresh_token(settings) is None
