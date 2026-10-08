"""Curated preparation documents and private, versioned study notes."""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl

from . import db

router = APIRouter(prefix="/api/interview-prep", tags=["interview-prep"])
PREP_ROOT = Path(__file__).resolve().parents[2] / "docs" / "interview-prep"
_lock = Lock()


def _custom_root() -> Path:
    return db.DATA_DIR / "private" / "interview-prep" / "workspaces"


def _workspace_ids() -> list[str]:
    curated = {p.parent.name for p in PREP_ROOT.glob("*/workspace.json")}
    custom = {p.stem for p in _custom_root().glob("*.json")}
    return sorted(curated | custom)


def _workspace(workspace_id: str) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", workspace_id):
        raise HTTPException(404, "准备专题不存在")
    curated = PREP_ROOT / workspace_id / "workspace.json"
    path = curated if curated.is_file() else _custom_root() / f"{workspace_id}.json"
    if not path.is_file():
        raise HTTPException(404, "准备专题不存在")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.stem, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _notes_path(workspace_id: str) -> Path:
    return db.DATA_DIR / "private" / "interview-prep" / f"{workspace_id}.json"


def _read_notes(workspace: dict) -> dict:
    path = _notes_path(workspace["id"])
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise HTTPException(500, "笔记文件读取失败，请保留原文件并检查备份") from exc
    return {**workspace["defaults"], "revision": 0, "updated_at": ""}


class Source(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    url: HttpUrl
    note: str = Field(default="", max_length=2000)


class NotesPatch(BaseModel):
    revision: int = Field(ge=0)
    interview_date: date | Literal[""] | None = None
    location: str | None = Field(default=None, max_length=500)
    jd: str | None = Field(default=None, max_length=60000)
    questions: str | None = Field(default=None, max_length=60000)
    notes: str | None = Field(default=None, max_length=120000)
    completed: list[str] | None = Field(default=None, max_length=200)
    sources: list[Source] | None = Field(default=None, max_length=300)


class WorkspaceCreate(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=160)
    team: str = Field(default="", max_length=200)
    interview_date: date | Literal[""] = ""
    summary: str = Field(default="", max_length=1000)
    jd: str = Field(default="", max_length=60000)


@router.get("")
def list_workspaces():
    with _lock:
        items = []
        for key in _workspace_ids():
            workspace = _workspace(key)
            notes = _read_notes(workspace)
            items.append({**{k: workspace[k] for k in ("id", "title", "team", "date_window", "summary")},
                          "interview_date": notes.get("interview_date", ""),
                          "document_count": len(workspace["documents"]),
                          "task_count": len(workspace["tasks"]),
                          "completed_count": len(set(notes.get("completed", [])) & {t["id"] for t in workspace["tasks"]}),
                          "updated_at": notes.get("updated_at", "")})
    return {"items": items}


@router.post("", status_code=201)
def create_workspace(payload: WorkspaceCreate):
    company, role = payload.company.strip(), payload.role.strip()
    if not company or not role:
        raise HTTPException(422, "请填写公司和岗位")
    workspace_id = f"prep-{uuid4().hex}"
    defaults = {"interview_date": str(payload.interview_date), "location": "", "jd": payload.jd,
                "questions": "", "notes": "", "completed": [], "sources": []}
    workspace = {"id": workspace_id, "title": f"{company} · {role}", "team": payload.team.strip(),
                 "date_window": str(payload.interview_date) or "时间待确认", "summary": payload.summary.strip(),
                 "documents": [], "tasks": [], "defaults": defaults}
    with _lock:
        _write_json(_custom_root() / f"{workspace_id}.json", workspace)
    return {"workspace": {k: v for k, v in workspace.items() if k != "defaults"}, "notes": _read_notes(workspace)}


@router.get("/{workspace_id}")
def get_workspace(workspace_id: str):
    workspace = _workspace(workspace_id)
    with _lock:
        notes = _read_notes(workspace)
    return {"workspace": {k: v for k, v in workspace.items() if k != "defaults"}, "notes": notes}


def _document(workspace_id: str, document_id: str) -> tuple[Path, str]:
    workspace = _workspace(workspace_id)
    document = next((d for d in workspace["documents"] if d["id"] == document_id), None)
    if not document:
        raise HTTPException(404, "资料不存在")
    return PREP_ROOT / workspace_id / f"{document_id}.md", document["title"]


@router.get("/{workspace_id}/documents/{document_id}")
def get_document(workspace_id: str, document_id: str):
    path, title = _document(workspace_id, document_id)
    return {"title": title, "content": path.read_text(encoding="utf-8")}


@router.get("/{workspace_id}/documents/{document_id}/download")
def download_document(workspace_id: str, document_id: str):
    path, _ = _document(workspace_id, document_id)
    return FileResponse(path, filename=path.name, media_type="text/markdown; charset=utf-8")


@router.patch("/{workspace_id}/notes")
def save_notes(workspace_id: str, payload: NotesPatch):
    workspace = _workspace(workspace_id)
    changes = payload.model_dump(mode="json", exclude_none=True, exclude={"revision"})
    allowed_tasks = {t["id"] for t in workspace["tasks"]}
    if set(changes.get("completed", [])) - allowed_tasks:
        raise HTTPException(422, "准备任务不存在")
    with _lock:
        current = _read_notes(workspace)
        if payload.revision != current["revision"]:
            raise HTTPException(409, "笔记已在其他窗口更新。请先导出当前内容，再重新加载后合并。")
        merged = {**current, **changes, "revision": current["revision"] + 1,
                  "updated_at": datetime.now(timezone.utc).isoformat()}
        # Atomic replacement leaves the previous document intact if writing fails.
        _write_json(_notes_path(workspace_id), merged)
    return {"notes": merged}


def register_routes(app) -> None:
    # Keep a flat route list for existing CareerOS inspection tools.
    for route in router.routes:
        app.add_api_route(route.path, route.endpoint, methods=route.methods,
                          tags=route.tags, name=route.name, status_code=route.status_code)
