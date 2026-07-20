from __future__ import annotations

import mimetypes
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ytcopilot import channel_profile as profile
from ytcopilot import content_authenticity, oauth, research, youtube_data
from ytcopilot.config import MissingConfig, get_settings
from ytcopilot.monetization import build_report, format_report_markdown

from . import jobs
from .auth import auth_is_configured, require_auth

# So /static/manifest.webmanifest (served by StaticFiles below, which is not
# behind Basic Auth) gets the right Content-Type — browsers' PWA-installability
# check fetches this in the background and needs it recognized as a manifest,
# not application/octet-stream.
mimetypes.add_type("application/manifest+json", ".webmanifest")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = Path("output")

# Whitelisted so /plan/files can't be used to read arbitrary paths.
PLAN_FILES = {"script.md", "chapters.json", "titles.md", "description.md", "thumbnail_brief.md", "thumbnail.png"}

@asynccontextmanager
async def _lifespan(app: FastAPI):
    if not auth_is_configured():
        print(
            "\n*** ytcopilot dashboard is running WITHOUT authentication "
            "(WEBAPP_USERNAME/WEBAPP_PASSWORD not set in .env). Every action here spends "
            "real API credits — do not expose this port beyond localhost. ***\n"
        )
    yield


app = FastAPI(title="ytcopilot dashboard", dependencies=[Depends(require_auth)], lifespan=_lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.middleware("http")
async def _allow_service_worker_root_scope(request: Request, call_next):
    # sw.js lives under /static/, whose default max scope is /static/ itself —
    # too narrow to control the actual app pages (/, /diagnose, ...), which is
    # required for the browser to treat this as an installable PWA at all. This
    # header is what lets base.html's register(..., {scope: "/"}) call succeed.
    response = await call_next(request)
    if request.url.path == "/static/sw.js":
        response.headers["Service-Worker-Allowed"] = "/"
    return response


def render(request: Request, template: str, active: str, **context):
    return templates.TemplateResponse(request, template, {"active": active, **context})


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    settings = get_settings()
    config_status = {
        "YouTube Data API": bool(settings.youtube_api_key),
        "YouTube Analytics (OAuth)": oauth.has_saved_credentials(settings),
        "Gemini (text + thumbnail images)": bool(settings.gemini_api_key),
    }
    # Only offer this once: show the refresh token to copy into
    # YOUTUBE_OAUTH_REFRESH_TOKEN until that env var is actually set, then
    # stop — no reason to keep exposing it on every dashboard load after.
    refresh_token_to_persist = None
    if not settings.youtube_oauth_refresh_token:
        refresh_token_to_persist = oauth.get_saved_refresh_token(settings)
    return render(
        request, "dashboard.html", "dashboard",
        channel_name=profile.CHANNEL_NAME,
        channel_handle=profile.CHANNEL_HANDLE,
        config_status=config_status,
        all_configured=all(config_status.values()),
        refresh_token_to_persist=refresh_token_to_persist,
        notice=request.query_params.get("notice"),
        error=request.query_params.get("error"),
    )


@app.get("/diagnose", response_class=HTMLResponse)
def diagnose_form(request: Request):
    return render(request, "diagnose.html", "diagnose")


@app.post("/diagnose", response_class=HTMLResponse)
def diagnose_submit(request: Request, channel: str = Form(...), use_analytics: bool = Form(False)):
    settings = get_settings()
    error = None
    report_md = None
    try:
        stats = youtube_data.get_channel_stats(settings, channel)
        watch = None
        if use_analytics:
            from ytcopilot import youtube_analytics
            watch = youtube_analytics.get_watch_hour_summary(settings)
        report = build_report(stats, watch)
        report_md = format_report_markdown(report)
    except MissingConfig as e:
        error = str(e)
    except Exception as e:  # noqa: BLE001 - surfaced to the user, not swallowed
        error = f"Lookup failed: {e}"
    return render(
        request, "diagnose.html", "diagnose",
        channel=channel, use_analytics=use_analytics, report_md=report_md, error=error,
    )


@app.get("/research", response_class=HTMLResponse)
def research_page(request: Request, niche: str = "", region: str = "US"):
    topics = trending = None
    error = None
    if niche:
        settings = get_settings()
        try:
            topics = research.suggest_topics(settings, niche, region=region)
            trending = research.trending_snapshot(settings, niche, region=region)
        except MissingConfig as e:
            error = str(e)
        except Exception as e:  # noqa: BLE001
            error = f"Search failed: {e}"
    return render(request, "research.html", "research", niche=niche, region=region, topics=topics, trending=trending, error=error)


@app.get("/schedule", response_class=HTMLResponse)
def schedule_page(request: Request, niche: str = "", use_analytics: bool = False):
    rec = None
    error = None
    if niche:
        settings = get_settings()
        try:
            rec = research.recommend_posting_schedule(settings, niche, use_analytics)
        except MissingConfig as e:
            error = str(e)
        except Exception as e:  # noqa: BLE001
            error = f"Lookup failed: {e}"
    return render(request, "schedule.html", "schedule", niche=niche, use_analytics=use_analytics, rec=rec, error=error)


@app.get("/rollout", response_class=HTMLResponse)
def rollout_page(request: Request, months: int = 3):
    plan_items = research.rollout_plan(months=months)
    md = research.format_rollout_markdown(plan_items)
    return render(request, "rollout.html", "rollout", months=months, md=md)


@app.get("/ideas", response_class=HTMLResponse)
def ideas_page(request: Request):
    ideas_with_patterns = [
        {**idea, "matched_patterns": profile.title_patterns_used(idea["pattern"])}
        for idea in profile.SEED_VIDEO_IDEAS
    ]
    return render(request, "ideas.html", "ideas", ideas=ideas_with_patterns, title_rule=profile.TITLE_RULE)


@app.get("/authenticity", response_class=HTMLResponse)
def authenticity_form(request: Request):
    return render(request, "authenticity.html", "authenticity", flags=None)


@app.post("/authenticity", response_class=HTMLResponse)
def authenticity_submit(
    request: Request,
    uploads_per_day: float = Form(1.0),
    ai_script_percent: int = Form(90),
    human_edit_pass: bool = Form(False),
    disclosure_on: bool = Form(False),
    template_rotation_count: int = Form(1),
    new_niches_this_month: int = Form(0),
    human_pov_stated: bool = Form(False),
):
    flags = content_authenticity.assess_authenticity_risk(
        uploads_per_day=uploads_per_day,
        ai_script_percent=ai_script_percent,
        human_edit_pass=human_edit_pass,
        disclosure_on=disclosure_on,
        template_rotation_count=template_rotation_count,
        new_niches_this_month=new_niches_this_month,
        human_pov_stated=human_pov_stated,
    )
    values = dict(
        uploads_per_day=uploads_per_day, ai_script_percent=ai_script_percent,
        human_edit_pass=human_edit_pass, disclosure_on=disclosure_on,
        template_rotation_count=template_rotation_count,
        new_niches_this_month=new_niches_this_month, human_pov_stated=human_pov_stated,
    )
    return render(request, "authenticity.html", "authenticity", flags=flags, values=values)


@app.get("/plan", response_class=HTMLResponse)
def plan_form(request: Request, topic: str = ""):
    return render(request, "plan.html", "plan", topic=topic)


@app.post("/plan")
def plan_submit(topic: str = Form(...), niche: str = Form(""), length_minutes: int = Form(10)):
    settings = get_settings()
    job = jobs.create_job(topic, niche, length_minutes)
    jobs.start_plan_job(job, settings, OUTPUT_DIR)
    return RedirectResponse(url=f"/plan/status/{job.id}", status_code=303)


@app.get("/plan/status/{job_id}", response_class=HTMLResponse)
def plan_status_page(request: Request, job_id: str):
    job = jobs.get_job(job_id)
    return render(request, "plan_status.html", "plan", job=job, job_id=job_id)


@app.get("/plan/status/{job_id}/json")
def plan_status_json(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        return JSONResponse({"status": "not_found"}, status_code=404)
    payload = {
        "status": job.status,
        "error": job.error,
        "steps": [{"name": s.name, "status": s.status} for s in job.steps],
    }
    if job.result:
        payload["result"] = {
            "slug": job.result["slug"],
            "chosen_title": job.result["chosen_title"],
            "titles": job.result["titles"],
            "script": job.result["script"],
            "description": job.result["description"],
            "chapters": job.result["chapters"],
            "thumbnail_brief": job.result["thumbnail_brief"].__dict__,
            "has_thumbnail_image": bool(job.result["thumbnail_image_path"]),
            "thumbnail_error": job.result["thumbnail_error"],
        }
    return JSONResponse(payload)


@app.get("/plan/files/{job_id}/{filename}")
def plan_file(job_id: str, filename: str):
    job = jobs.get_job(job_id)
    if not job or not job.result or filename not in PLAN_FILES:
        return JSONResponse({"error": "not found"}, status_code=404)
    path = Path(job.result["video_dir"]) / filename
    if not path.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path)


@app.get("/auth/start")
def auth_start():
    settings = get_settings()
    try:
        flow = oauth.build_web_flow(settings, settings.webapp_oauth_redirect_uri)
    except MissingConfig as e:
        return RedirectResponse(url=f"/?error={e}")
    auth_url, state = flow.authorization_url(
        access_type="offline", prompt="consent", include_granted_scopes="true"
    )
    oauth.store_code_verifier(state, flow.code_verifier)
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
def auth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        return RedirectResponse(url=f"/?error={error}")
    if not code:
        return RedirectResponse(url="/?error=No authorization code returned by Google.")
    settings = get_settings()
    try:
        code_verifier = oauth.pop_code_verifier(state)
        flow = oauth.build_web_flow(settings, settings.webapp_oauth_redirect_uri, code_verifier=code_verifier)
        flow.fetch_token(code=code)
        oauth.save_credentials(settings, flow.credentials)
    except Exception as e:  # noqa: BLE001
        return RedirectResponse(url=f"/?error=Authentication failed: {e}")
    return RedirectResponse(url="/?notice=YouTube Analytics connected.")
