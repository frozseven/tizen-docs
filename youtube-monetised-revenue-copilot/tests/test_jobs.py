from pathlib import Path

from webapp import jobs
from ytcopilot import pipeline
from ytcopilot.config import Settings


def test_create_job_has_one_step_per_pipeline_step():
    job = jobs.create_job("Test topic", "personal finance", 5)
    assert [s.name for s in job.steps] == pipeline.STEP_NAMES
    assert all(s.status == "pending" for s in job.steps)
    assert job.status == "running"


def test_get_job_returns_none_for_unknown_id():
    assert jobs.get_job("does-not-exist") is None


def test_start_plan_job_reports_progress_and_completes(monkeypatch, tmp_path):
    def fake_run_plan_pipeline(settings, topic, niche, length_minutes, out_dir, on_progress=None):
        for i, name in enumerate(pipeline.STEP_NAMES):
            if on_progress:
                on_progress(i, name, "active")
                on_progress(i, name, "done")
        return {
            "video_dir": out_dir / "test-topic",
            "slug": "test-topic",
            "script": "script text",
            "chapters": [{"timestamp": "0:00", "label": "Open"}],
            "titles": ["Title One"],
            "chosen_title": "Title One",
            "description": "description text",
            "thumbnail_brief": type("B", (), {"__dict__": {"composition": "x"}})(),
            "thumbnail_image_path": None,
            "thumbnail_error": "GEMINI_API_KEY is not set.",
        }

    monkeypatch.setattr(pipeline, "run_plan_pipeline", fake_run_plan_pipeline)

    job = jobs.create_job("Test topic", "", 5)
    jobs._run(job, Settings(), tmp_path)  # run synchronously for a deterministic test

    assert job.status == "done"
    assert all(s.status == "done" for s in job.steps)
    assert job.result["chosen_title"] == "Title One"


def test_start_plan_job_marks_active_step_as_error_on_exception(monkeypatch, tmp_path):
    def failing_pipeline(settings, topic, niche, length_minutes, out_dir, on_progress=None):
        on_progress(0, pipeline.STEP_NAMES[0], "active")
        raise RuntimeError("boom")

    monkeypatch.setattr(pipeline, "run_plan_pipeline", failing_pipeline)

    job = jobs.create_job("Test topic", "", 5)
    jobs._run(job, Settings(), tmp_path)

    assert job.status == "error"
    assert "boom" in job.error
    assert job.steps[0].status == "error"
