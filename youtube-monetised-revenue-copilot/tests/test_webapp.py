from fastapi.testclient import TestClient

from webapp import app as app_module

client = TestClient(app_module.app)


def test_dashboard_loads():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "The Wealth Sheikh" in resp.text


def test_diagnose_form_loads():
    resp = client.get("/diagnose")
    assert resp.status_code == 200
    assert "Diagnose" in resp.text


def test_diagnose_submit_without_api_key_shows_error(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    resp = client.post("/diagnose", data={"channel": "@The.Wealth.Sheikh"})
    assert resp.status_code == 200
    assert "YOUTUBE_API_KEY" in resp.text


def test_research_page_with_no_query_shows_only_form():
    resp = client.get("/research")
    assert resp.status_code == 200
    assert "Top recent videos" not in resp.text


def test_research_page_without_api_key_shows_error(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    resp = client.get("/research", params={"niche": "personal finance"})
    assert resp.status_code == 200
    assert "YOUTUBE_API_KEY" in resp.text


def test_rollout_page_renders_weeks():
    resp = client.get("/rollout")
    assert resp.status_code == 200
    assert "Week 1" in resp.text


def test_ideas_page_lists_seed_ideas():
    resp = client.get("/ideas")
    assert resp.status_code == 200
    assert "Why Your Raise Never Makes You Richer" in resp.text


def test_authenticity_form_loads():
    resp = client.get("/authenticity")
    assert resp.status_code == 200


def test_authenticity_submit_computes_flags():
    resp = client.post("/authenticity", data={
        "uploads_per_day": "1",
        "ai_script_percent": "90",
        "human_edit_pass": "true",
        "disclosure_on": "true",
        "template_rotation_count": "1",
        "new_niches_this_month": "0",
        "human_pov_stated": "true",
    })
    assert resp.status_code == 200
    assert "Template sameness" in resp.text


def test_authenticity_submit_unchecked_boxes_are_false():
    resp = client.post("/authenticity", data={
        "uploads_per_day": "1",
        "ai_script_percent": "90",
        "template_rotation_count": "3",
        "new_niches_this_month": "0",
        # human_edit_pass, disclosure_on, human_pov_stated intentionally omitted
    })
    assert resp.status_code == 200
    assert "Disclosure toggle is off" in resp.text


def test_plan_form_loads():
    resp = client.get("/plan")
    assert resp.status_code == 200


def test_plan_form_prefills_topic_from_query():
    resp = client.get("/plan", params={"topic": "Test video idea"})
    assert resp.status_code == 200
    assert "Test video idea" in resp.text


def test_plan_submit_creates_job_and_redirects(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "OUTPUT_DIR", tmp_path)
    resp = client.post(
        "/plan", data={"topic": "Test video", "niche": "", "length_minutes": "5"}, follow_redirects=False
    )
    assert resp.status_code == 303
    location = resp.headers["location"]
    assert location.startswith("/plan/status/")

    status_resp = client.get(location)
    assert status_resp.status_code == 200
    assert "Generating" in status_resp.text


def test_plan_status_unknown_job_id_handled_gracefully():
    resp = client.get("/plan/status/does-not-exist")
    assert resp.status_code == 200
    assert "not found" in resp.text.lower()


def test_plan_status_json_unknown_job_returns_404():
    resp = client.get("/plan/status/does-not-exist/json")
    assert resp.status_code == 404


def test_plan_file_rejects_non_whitelisted_filename():
    resp = client.get("/plan/files/some-job-id/../../etc/passwd")
    assert resp.status_code == 404


def test_basic_auth_blocks_when_configured(monkeypatch):
    monkeypatch.setenv("WEBAPP_USERNAME", "admin")
    monkeypatch.setenv("WEBAPP_PASSWORD", "secret")

    resp = client.get("/")
    assert resp.status_code == 401

    resp = client.get("/", auth=("admin", "wrong"))
    assert resp.status_code == 401

    resp = client.get("/", auth=("admin", "secret"))
    assert resp.status_code == 200


def test_no_auth_required_when_unconfigured(monkeypatch):
    monkeypatch.delenv("WEBAPP_USERNAME", raising=False)
    monkeypatch.delenv("WEBAPP_PASSWORD", raising=False)
    resp = client.get("/")
    assert resp.status_code == 200
