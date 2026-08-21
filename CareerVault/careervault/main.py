from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .migration_review import complete_migration_review
from .models import ExperienceCreate, ExperienceUpdate, InboxCreate, MigrationReviewComplete, ProfileUpdate
from .store import (
    ROOT,
    add_inbox,
    create_experience,
    dashboard,
    delete_experience,
    delete_inbox,
    get_experience,
    get_profile,
    git_snapshot,
    git_status,
    list_experiences,
    list_inbox,
    list_files,
    rank_experiences,
    read_text_file,
    save_attachment,
    save_vault_upload,
    safe_vault_path,
    update_experience,
    update_profile,
    write_text_file,
)

app = FastAPI(title="CareerVault", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765", "http://127.0.0.1:8766", "http://localhost:8766"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _jobpilot_eligible(item: dict) -> bool:
    return bool(item.get("resume_ready")) and item.get("migration_review") != "required"


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
def health():
    return {"ok": True, "version": __version__, "root": str(ROOT)}


@app.get("/api/dashboard")
def api_dashboard():
    data = dashboard()
    items = list_experiences()
    data["resume_ready_count"] = sum(1 for x in items if _jobpilot_eligible(x))
    data["migration_review_count"] = sum(1 for x in items if x.get("migration_review") == "required")
    return data


@app.get("/api/profile")
def api_profile():
    return get_profile()


@app.put("/api/profile")
def api_update_profile(payload: ProfileUpdate):
    return update_profile(payload.model_dump())


@app.get("/api/experiences")
def api_experiences():
    return list_experiences()


@app.post("/api/experiences")
def api_create_experience(payload: ExperienceCreate):
    return create_experience(payload.model_dump())


@app.get("/api/experiences/{experience_id}")
def api_get_experience(experience_id: str):
    try:
        return get_experience(experience_id)
    except FileNotFoundError:
        raise HTTPException(404, "Experience not found")


@app.patch("/api/experiences/{experience_id}")
def api_update_experience(experience_id: str, payload: ExperienceUpdate):
    try:
        changes = payload.model_dump(exclude_unset=True)
        return update_experience(experience_id, changes)
    except FileNotFoundError:
        raise HTTPException(404, "Experience not found")


@app.post("/api/experiences/{experience_id}/migration-review")
def api_complete_migration_review(experience_id: str, payload: MigrationReviewComplete):
    try:
        return complete_migration_review(experience_id, resume_ready=payload.resume_ready)
    except FileNotFoundError:
        raise HTTPException(404, "Experience not found")


@app.delete("/api/experiences/{experience_id}")
def api_delete_experience(experience_id: str):
    try:
        delete_experience(experience_id)
        return {"ok": True}
    except FileNotFoundError:
        raise HTTPException(404, "Experience not found")


@app.post("/api/experiences/{experience_id}/attachments")
async def api_add_attachment(experience_id: str, file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large; max 50 MB")
    try:
        return save_attachment(experience_id, file.filename or "attachment.bin", data)
    except FileNotFoundError:
        raise HTTPException(404, "Experience not found")


@app.get("/api/inbox")
def api_inbox():
    return list_inbox()


@app.post("/api/inbox")
def api_add_inbox(payload: InboxCreate):
    return add_inbox(payload.model_dump())


@app.delete("/api/inbox/{item_id}")
def api_delete_inbox(item_id: str):
    try:
        delete_inbox(item_id)
        return {"ok": True}
    except FileNotFoundError:
        raise HTTPException(404, "Inbox item not found")


@app.get("/api/files")
def api_files():
    return {"items": list_files()}


@app.get("/api/files/read")
def api_read_file(path: str):
    try:
        return read_text_file(path)
    except FileNotFoundError:
        raise HTTPException(404, "File not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.put("/api/files/write")
def api_write_file(payload: dict):
    try:
        return write_text_file(str(payload.get("path") or ""), str(payload.get("content") or ""))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/files/upload")
async def api_upload_file(file: UploadFile = File(...), directory: str = Form("inbox/files")):
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large; max 50 MB")
    try:
        return save_vault_upload(file.filename or "upload.bin", data, directory=directory)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.get("/api/files/raw")
def api_raw_file(path: str):
    try:
        target = safe_vault_path(path)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target)


@app.get("/api/git/status")
def api_git_status():
    return git_status()


@app.post("/api/git/snapshot")
def api_git_snapshot(payload: dict):
    return git_snapshot(str(payload.get("message", "Update CareerVault")))


# ---- JobPilot integration contract ----
@app.get("/api/jobpilot/profile")
def jobpilot_profile():
    return get_profile()


@app.get("/api/jobpilot/experiences")
def jobpilot_experiences(resume_ready: bool = True):
    items = list_experiences()
    if resume_ready:
        items = [x for x in items if _jobpilot_eligible(x)]
    return items


@app.post("/api/jobpilot/context")
def jobpilot_context(payload: dict):
    jd = str(payload.get("jd") or payload.get("query") or "")
    limit = max(1, min(int(payload.get("limit", 6)), 20))
    ranked = rank_experiences(jd, only_resume_ready=False)
    ranked = [x for x in ranked if _jobpilot_eligible(x)]
    return {
        "schema_version": 1,
        "profile": get_profile(),
        "experiences": ranked[:limit],
        "source": "CareerVault",
        "version": __version__,
    }
