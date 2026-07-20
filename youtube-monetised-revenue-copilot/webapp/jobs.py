"""In-memory background job store for the `plan` pipeline.

A single-user local dashboard doesn't need Celery/Redis — a thread plus a
dict is enough, and it keeps the whole app runnable with one `uvicorn`
command. Jobs are not persisted across restarts.
"""

from __future__ import annotations

import threading
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from ytcopilot import pipeline
from ytcopilot.config import Settings

_JOBS: dict[str, "Job"] = {}
_LOCK = threading.Lock()


@dataclass
class Step:
    name: str
    status: str = "pending"  # pending | active | done | error


@dataclass
class Job:
    id: str
    topic: str
    niche: str
    length_minutes: int
    steps: list[Step]
    status: str = "running"  # running | done | error
    error: str | None = None
    result: dict | None = None


def create_job(topic: str, niche: str, length_minutes: int) -> Job:
    job = Job(
        id=str(uuid.uuid4()),
        topic=topic,
        niche=niche,
        length_minutes=length_minutes,
        steps=[Step(name) for name in pipeline.STEP_NAMES],
    )
    with _LOCK:
        _JOBS[job.id] = job
    return job


def get_job(job_id: str) -> Job | None:
    with _LOCK:
        return _JOBS.get(job_id)


def start_plan_job(job: Job, settings: Settings, out_dir: Path) -> None:
    thread = threading.Thread(target=_run, args=(job, settings, out_dir), daemon=True)
    thread.start()


def _run(job: Job, settings: Settings, out_dir: Path) -> None:
    def on_progress(index: int, name: str, status: str) -> None:
        with _LOCK:
            job.steps[index].status = status

    try:
        result = pipeline.run_plan_pipeline(
            settings, job.topic, job.niche, job.length_minutes, out_dir, on_progress=on_progress
        )
        with _LOCK:
            job.result = result
            job.status = "done"
    except Exception as e:  # noqa: BLE001 - surfaced to the UI, not swallowed
        with _LOCK:
            job.status = "error"
            job.error = f"{e}\n\n{traceback.format_exc(limit=3)}"
            for step in job.steps:
                if step.status == "active":
                    step.status = "error"
