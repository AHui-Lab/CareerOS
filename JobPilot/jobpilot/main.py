from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
from urllib.parse import quote
import email
import email.header
import email.utils
import imaplib
import re
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, db
from .ai import enrich_with_ai, enabled as opportunity_ai_enabled
from .autofill import build_flat_package, build_structured_autofill
from .career_selection import filter_selected, rank_experiences
from .careervault import (
    all_resume_ready as careervault_all_resume_ready,
    context_for_jd as careervault_context,
    health as careervault_health,
)
from .opportunity_meta import JOB_CATEGORIES, get_category_map, init_opportunity_meta, set_category
from .parser import fetch_page, finalize_parsed, heuristic_parse, load_profile as legacy_match_profile, normalize_text
from .resume import (
    ai_enabled as resume_ai_enabled,
    extract_resume_structured,
    extract_text_from_resume,
    generate_docx_bytes,
    generate_pdf_bytes,
    generate_tailored_resume,
)
from .security import UnsafeUrlError

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / "static"
load_dotenv(ROOT / ".env")
db.init_db()
init_opportunity_meta()

app = FastAPI(title="JobPilot", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.mount("/static", StaticFiles(directory=STATIC), name="static")

ALLOWED_STATUSES = {"inbox", "interested", "preparing", "applied", "interview", "offer", "rejected", "ignored"}
ALLOWED_CATEGORIES = {"education", "work", "internship", "project", "campus", "research", "award", "certificate", "skill", "other"}
ALLOWED_EVENT_TYPES = {"application", "written_test", "interview", "deadline", "follow_up", "other"}


class UrlImport(BaseModel):
    url: str = Field(min_length=8, max_length=4096)


class PageImport(BaseModel):
    url: str = Field(default="", max_length=4096)
    title: str = Field(default="", max_length=500)
    text: str = Field(min_length=10, max_length=200_000)
    context: dict[str, Any] = Field(default_factory=dict)


class TextImport(BaseModel):
    text: str = Field(min_length=10, max_length=200_000)
    title: str = Field(default="招聘备忘", max_length=500)


class StatusPatch(BaseModel):
    status: str


class OpportunityCategoryPatch(BaseModel):
    category: str


class OpportunityEdit(BaseModel):
    company: str | None = Field(default=None, max_length=120)
    role: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    deadline: str | None = Field(default=None, max_length=80)
    referral_code: str | None = Field(default=None, max_length=300)
    jd_text: str | None = Field(default=None, max_length=60_000)
    note: str | None = Field(default=None, max_length=4000)


class ScheduleEventPayload(BaseModel):
    event_type: str = "other"
    title: str = Field(default="", max_length=200)
    event_date: str = Field(default="", max_length=20)
    event_time: str = Field(default="", max_length=20)
    location: str = Field(default="", max_length=200)
    notes: str = Field(default="", max_length=4000)
    opportunity_id: int | None = None


class ScheduleEventPatch(ScheduleEventPayload):
    event_type: str | None = None
    title: str | None = None
    event_date: str | None = None
    event_time: str | None = None
    location: str | None = None
    notes: str | None = None
    opportunity_id: int | None = None


class EmailSettingsPayload(BaseModel):
    imap_host: str = Field(default="imap.gmail.com", max_length=200)
    imap_port: int = Field(default=993, ge=1, le=65535)
    username: str = Field(default="", max_length=320)
    password: str = Field(default="", max_length=500)
    folder: str = Field(default="INBOX", max_length=120)


class EmailImportItem(BaseModel):
    email_id: int
    opportunity_id: int | None = None


class EmailImportPayload(BaseModel):
    items: list[EmailImportItem] = Field(default_factory=list)


class EmailLinkPayload(BaseModel):
    opportunity_id: int | None = None


class ProfilePatch(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    id_type: str | None = None
    id_number: str | None = None
    ethnicity: str | None = None
    native_place: str | None = None
    political_status: str | None = None
    marital_status: str | None = None
    household_registration: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    photo_path: str | None = None
    current_city: str | None = None
    school: str | None = None
    college: str | None = None
    major: str | None = None
    degree: str | None = None
    graduation_date: str | None = None
    education_start_date: str | None = None
    degree_type: str | None = None
    gpa: str | None = None
    rank: str | None = None
    website: str | None = None
    portfolio_url: str | None = None
    github_url: str | None = None
    summary: str | None = None


class ExperiencePayload(BaseModel):
    category: str = "other"
    title: str = ""
    organization: str = ""
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    description: str = ""
    highlights: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ExperiencePatch(BaseModel):
    category: str | None = None
    title: str | None = None
    organization: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None
    description: str | None = None
    highlights: list[str] | None = None
    tags: list[str] | None = None


class InterviewQuestionPayload(BaseModel):
    question_type: str = "interview"
    source_type: str = "personal"
    role_category: str = Field(default="", max_length=120)
    company: str = Field(default="", max_length=160)
    opportunity_id: int | None = None
    question: str = Field(default="", max_length=8000)
    answer: str = Field(default="", max_length=12000)
    feeling: str = Field(default="", max_length=6000)
    tags: list[str] = Field(default_factory=list)
    event_date: str = Field(default="", max_length=20)


class InterviewQuestionPatch(InterviewQuestionPayload):
    question_type: str | None = None
    source_type: str | None = None
    role_category: str | None = None
    company: str | None = None
    opportunity_id: int | None = None
    question: str | None = None
    answer: str | None = None
    feeling: str | None = None
    tags: list[str] | None = None
    event_date: str | None = None


class RoleFieldSetPayload(BaseModel):
    role_category: str = Field(default="", max_length=120)
    title: str = Field(default="", max_length=160)
    self_evaluation: str = Field(default="", max_length=8000)
    strengths: str = Field(default="", max_length=8000)
    skills: list[str] = Field(default_factory=list)
    common_answers: dict[str, str] = Field(default_factory=dict)
    notes: str = Field(default="", max_length=6000)


class RoleFieldSetPatch(RoleFieldSetPayload):
    role_category: str | None = None
    title: str | None = None
    self_evaluation: str | None = None
    strengths: str | None = None
    skills: list[str] | None = None
    common_answers: dict[str, str] | None = None
    notes: str | None = None


class CareerRecommendationRequest(BaseModel):
    opportunity_id: int | None = None
    target_company: str = Field(default="", max_length=120)
    target_role: str = Field(default="", max_length=160)
    jd: str = Field(default="", max_length=60_000)


class ResumeGenerate(BaseModel):
    opportunity_id: int | None = None
    target_company: str = Field(default="", max_length=120)
    target_role: str = Field(default="", max_length=160)
    jd: str = Field(default="", max_length=60_000)
    experience_ids: list[int] = Field(default_factory=list)
    # None preserves the V0.3.0 automatic CareerVault path. A list means the user explicitly reviewed selection.
    careervault_experience_ids: list[str] | None = None


def _recover_source_url(item: dict[str, Any]) -> str:
    direct = str(item.get("source_url") or "").strip()
    if direct:
        return direct
    context = item.get("page_context") if isinstance(item.get("page_context"), dict) else {}
    for key in ("source_url", "page_url", "canonical_url", "url"):
        value = str(context.get(key) or "").strip()
        if value.startswith(("http://", "https://")):
            return value
    hostname = str(context.get("hostname") or "").strip().strip("/")
    pathname = str(context.get("pathname") or "").strip()
    if hostname:
        if pathname and not pathname.startswith("/"):
            pathname = "/" + pathname
        return f"https://{hostname}{pathname}"
    return ""


def _decorate_opportunities(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_map = get_category_map()
    decorated: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row["job_category"] = category_map.get(int(row.get("id") or 0), "unclassified")
        row["source_url"] = _recover_source_url(row)
        decorated.append(row)
    return decorated


def _merge_profile(local_profile: dict[str, Any], cv_profile: dict[str, Any]) -> dict[str, Any]:
    return {**local_profile, **{k: v for k, v in (cv_profile or {}).items() if str(v or "").strip()}}


def _resolve_target(
    opportunity_id: int | None,
    target_company: str,
    target_role: str,
    jd: str,
) -> tuple[dict[str, str], dict[str, Any] | None]:
    company = target_company.strip()
    role = target_role.strip()
    target_jd = jd.strip()
    opportunity: dict[str, Any] | None = None
    if opportunity_id:
        opportunity = db.get_opportunity(opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="目标机会不存在")
        company = company or str(opportunity.get("company") or "")
        role = role or str(opportunity.get("role") or "")
        target_jd = target_jd or str(opportunity.get("description") or opportunity.get("raw_text") or "")
    return {
        "target_company": company,
        "target_role": role,
        "target_jd": target_jd[:45_000],
    }, opportunity


async def parse_and_store(*, url: str, title: str, text: str, source_type: str, page_context: dict[str, Any] | None = None, refresh_existing: bool = False):
    existing = db.find_by_url(url) if url else None
    if existing and not refresh_existing:
        return {"item": existing, "duplicate": True, "refreshed": False, "ai_enabled": opportunity_ai_enabled()}
    base = heuristic_parse(url=url, title=title, text=text, source_type=source_type, page_context=page_context)
    try:
        ai_candidate = await enrich_with_ai(base, legacy_match_profile())
        parsed = finalize_parsed(base, ai_candidate)
    except Exception:
        parsed = base
    if existing and refresh_existing:
        item = db.refresh_opportunity(existing["id"], parsed, preserve_status=True)
        return {"item": item, "duplicate": True, "refreshed": True, "ai_enabled": opportunity_ai_enabled()}
    item = db.insert_opportunity(parsed)
    return {"item": item, "duplicate": False, "refreshed": False, "ai_enabled": opportunity_ai_enabled()}


@app.get("/")
async def home():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    cv = await careervault_health()
    return {
        "ok": True,
        "version": __version__,
        "api_contract": 2,
        "ai_enabled": resume_ai_enabled(),
        "opportunity_ai_enabled": opportunity_ai_enabled(),
        "db": str(db.DB_PATH),
        "data": db.data_status(),
        "careervault": cv,
        "resume_source": "careervault-primary",
    }


# --- opportunity memo ---
@app.get("/api/opportunities")
async def opportunities():
    return {"items": _decorate_opportunities(db.list_opportunities()), "job_categories": JOB_CATEGORIES}


@app.post("/api/opportunities/import-url")
async def import_url(payload: UrlImport):
    try:
        title, text, context = await fetch_page(payload.url)
        return await parse_and_store(url=payload.url.strip(), title=title, text=text, source_type="url", page_context=context)
    except UnsafeUrlError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"网页抓取失败：{exc}") from exc


@app.post("/api/opportunities/import-page")
async def import_page(payload: PageImport):
    context = dict(payload.context or {})
    if payload.url.strip():
        context.setdefault("page_url", payload.url.strip())
    return await parse_and_store(
        url=payload.url.strip(), title=normalize_text(payload.title), text=normalize_text(payload.text),
        source_type="browser", page_context=context, refresh_existing=True,
    )


@app.post("/api/opportunities/import-text")
async def import_text(payload: TextImport):
    return await parse_and_store(url="", title=normalize_text(payload.title), text=normalize_text(payload.text), source_type="text")


@app.patch("/api/opportunities/{opportunity_id}/status")
async def patch_status(opportunity_id: int, payload: StatusPatch):
    if payload.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="未知状态")
    item = db.update_status(opportunity_id, payload.status)
    if not item:
        raise HTTPException(status_code=404, detail="机会不存在")
    return {"item": item}


@app.post("/api/opportunities/{opportunity_id}/status")
async def post_status(opportunity_id: int, payload: StatusPatch):
    return await patch_status(opportunity_id, payload)


@app.patch("/api/opportunities/{opportunity_id}/category")
async def patch_opportunity_category(opportunity_id: int, payload: OpportunityCategoryPatch):
    if payload.category not in JOB_CATEGORIES:
        raise HTTPException(status_code=400, detail="未知岗位类别")
    try:
        item = set_category(opportunity_id, payload.category)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail="机会不存在")
    return {"item": item}


@app.post("/api/opportunities/{opportunity_id}/category")
async def post_opportunity_category(opportunity_id: int, payload: OpportunityCategoryPatch):
    return await patch_opportunity_category(opportunity_id, payload)


@app.patch("/api/opportunities/{opportunity_id}")
async def patch_opportunity(opportunity_id: int, payload: OpportunityEdit):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="没有需要修改的字段")
    item = db.edit_opportunity(opportunity_id, fields)
    if not item:
        raise HTTPException(status_code=404, detail="机会不存在")
    return {"item": item}


@app.post("/api/opportunities/{opportunity_id}/edit")
async def post_edit_opportunity(opportunity_id: int, payload: OpportunityEdit):
    return await patch_opportunity(opportunity_id, payload)


@app.delete("/api/opportunities/{opportunity_id}")
async def delete_opportunity(opportunity_id: int):
    if not db.delete_opportunity(opportunity_id):
        raise HTTPException(status_code=404, detail="机会不存在")
    return {"ok": True}


# --- application calendar ---
@app.get("/api/schedule-events")
async def schedule_events(start: str = "", end: str = ""):
    return {"items": db.list_schedule_events(start=start, end=end)}


@app.post("/api/schedule-events")
async def create_schedule_event(payload: ScheduleEventPayload):
    if payload.event_type not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="未知日程类型")
    if not payload.title.strip() or not payload.event_date.strip():
        raise HTTPException(status_code=400, detail="日程标题和日期不能为空")
    if payload.opportunity_id and not db.get_opportunity(payload.opportunity_id):
        raise HTTPException(status_code=404, detail="关联岗位不存在")
    return {"item": db.insert_schedule_event(payload.model_dump())}


@app.patch("/api/schedule-events/{event_id}")
async def patch_schedule_event(event_id: int, payload: ScheduleEventPatch):
    fields = payload.model_dump(exclude_unset=True)
    if "event_type" in fields and fields["event_type"] not in ALLOWED_EVENT_TYPES:
        raise HTTPException(status_code=400, detail="未知日程类型")
    if "opportunity_id" in fields and fields["opportunity_id"] and not db.get_opportunity(fields["opportunity_id"]):
        raise HTTPException(status_code=404, detail="关联岗位不存在")
    item = db.update_schedule_event(event_id, fields)
    if not item:
        raise HTTPException(status_code=404, detail="日程不存在")
    return {"item": item}


@app.delete("/api/schedule-events/{event_id}")
async def remove_schedule_event(event_id: int):
    if not db.delete_schedule_event(event_id):
        raise HTTPException(status_code=404, detail="日程不存在")
    return {"ok": True}


# --- incremental email tracking ---
def _decode_email_header(value: str) -> str:
    parts = email.header.decode_header(value or "")
    decoded_parts: list[str] = []
    for part, charset in parts:
        if not isinstance(part, bytes):
            decoded_parts.append(str(part))
            continue
        encoding = str(charset or "utf-8").strip()
        try:
            decoded_parts.append(part.decode(encoding, errors="replace"))
        except (LookupError, UnicodeError):
            # Some mail clients, including QQ mailbox messages, use the
            # non-standard `unknown-8bit` label. Keep the message and fall
            # back to encodings that can safely represent the raw bytes.
            try:
                decoded_parts.append(part.decode("utf-8", errors="replace"))
            except UnicodeError:
                decoded_parts.append(part.decode("latin-1", errors="replace"))
    return "".join(decoded_parts).strip()


def _email_body(message: email.message.Message) -> str:
    chunks: list[str] = []
    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.get_content_maintype() != "text" or part.get_content_disposition() == "attachment":
            continue
        try:
            text = part.get_payload(decode=True)
            charset = part.get_content_charset() or "utf-8"
            decoded = (text or b"").decode(charset, errors="replace") if isinstance(text, bytes) else str(text or "")
        except Exception:
            decoded = str(part.get_payload() or "")
        if part.get_content_subtype() == "html":
            decoded = re.sub(r"<[^>]+>", " ", decoded)
        chunks.append(re.sub(r"\s+", " ", decoded).strip())
    return "\n".join(x for x in chunks if x)[:12000]


def _sync_email_messages() -> dict[str, Any]:
    settings = db.get_email_settings()
    password = db.get_email_password()
    required = [settings.get("imap_host"), settings.get("username"), password]
    if not all(str(x or "").strip() for x in required):
        raise HTTPException(status_code=400, detail="请先在设置中填写 IMAP 地址、邮箱账号和密码。")
    client = None
    try:
        client = imaplib.IMAP4_SSL(str(settings["imap_host"]), int(settings.get("imap_port") or 993))
        client.login(str(settings["username"]), password)
        status, _ = client.select(str(settings.get("folder") or "INBOX"), readonly=True)
        if status != "OK":
            raise ValueError(f"无法打开邮箱文件夹：{settings.get('folder') or 'INBOX'}")
        last_uid = int(settings.get("last_uid") or 0)
        status, data = client.uid("SEARCH", None, f"UID {last_uid + 1}:*")
        if status != "OK":
            raise ValueError("无法读取邮箱新邮件列表")
        uids = [int(x) for x in (data[0] or b"").split()]
        # Protect the local app from an unexpectedly huge first sync.
        selected_uids = uids[-20:]
        messages: list[dict[str, Any]] = []
        for uid in selected_uids:
            status, fetched = client.uid("FETCH", str(uid), "(RFC822)")
            if status != "OK":
                continue
            raw = next((part[1] for part in fetched if isinstance(part, tuple) and len(part) > 1), None)
            if not raw:
                continue
            message = email.message_from_bytes(raw)
            body = _email_body(message)
            received = email.utils.parsedate_to_datetime(message.get("Date", "")) if message.get("Date") else None
            messages.append({
                "uid": uid,
                "message_id": _decode_email_header(message.get("Message-ID", "")),
                "sender": _decode_email_header(message.get("From", "")),
                "subject": _decode_email_header(message.get("Subject", "(无主题)")) or "(无主题)",
                "received_at": received.isoformat(sep=" ", timespec="minutes") if received else str(message.get("Date", "")),
                "snippet": body[:240],
                "body": body,
            })
        added = db.insert_email_messages(messages)
        if uids:
            db.advance_email_uid(max(uids))
        return {"added": added, "checked": len(uids), "last_uid": max(uids or [last_uid]), "items": db.list_email_messages()}
    except imaplib.IMAP4.error as exc:
        raise HTTPException(status_code=502, detail=f"邮箱登录或读取失败：{exc}") from exc
    except OSError as exc:
        raise HTTPException(status_code=502, detail=f"无法连接邮箱服务器：{exc}") from exc
    finally:
        if client is not None:
            try: client.logout()
            except Exception: pass


@app.get("/api/email/settings")
async def email_settings():
    return {"settings": db.get_email_settings()}


@app.post("/api/email/settings")
async def update_email_settings(payload: EmailSettingsPayload):
    current = db.get_email_settings()
    fields = payload.model_dump()
    if not fields["password"]:
        fields["password"] = db.get_email_password()
    if fields["username"] != current.get("username") or fields["imap_host"] != current.get("imap_host") or fields["folder"] != current.get("folder"):
        fields["last_uid"] = 0
    db.save_email_settings(fields)
    return {"settings": db.get_email_settings()}


@app.post("/api/email/sync")
async def sync_email():
    return _sync_email_messages()


@app.get("/api/email/messages")
async def email_messages():
    return {"items": db.list_email_messages(include_ignored=True)}


@app.post("/api/email/messages/{email_id}/ignore")
async def ignore_email_message(email_id: int):
    item = db.update_email_message(email_id, status="ignored")
    if not item:
        raise HTTPException(status_code=404, detail="邮件不存在")
    return {"item": item}


@app.post("/api/email/messages/ignore-pending")
async def ignore_pending_email_messages():
    return {"ignored": db.ignore_pending_email_messages(), "items": db.list_email_messages(include_ignored=True)}


@app.post("/api/email/messages/{email_id}/link")
async def link_email_message(email_id: int, payload: EmailLinkPayload):
    if payload.opportunity_id and not db.get_opportunity(payload.opportunity_id):
        raise HTTPException(status_code=404, detail="关联岗位不存在")
    item = db.update_email_message(email_id, status="imported", opportunity_id=payload.opportunity_id, clear_opportunity=payload.opportunity_id is None)
    if not item:
        raise HTTPException(status_code=404, detail="邮件不存在")
    return {"item": item}


@app.post("/api/email/import")
async def import_email_messages(payload: EmailImportPayload):
    if not payload.items:
        raise HTTPException(status_code=400, detail="请至少选择一封邮件。")
    imported = 0
    for selected in payload.items:
        message = next((x for x in db.list_email_messages(include_ignored=True) if int(x["id"]) == selected.email_id), None)
        if not message:
            raise HTTPException(status_code=404, detail=f"邮件不存在：{selected.email_id}")
        if selected.opportunity_id and not db.get_opportunity(selected.opportunity_id):
            raise HTTPException(status_code=404, detail="关联岗位不存在")
        if selected.opportunity_id:
            opportunity = db.get_opportunity(selected.opportunity_id) or {}
            email_note = f"邮件跟踪：{message.get('received_at')} · {message.get('subject')} · {message.get('sender')}"
            old_note = str(opportunity.get("note") or "").strip()
            db.edit_opportunity(selected.opportunity_id, {"note": f"{old_note}\n{email_note}".strip()})
        db.update_email_message(selected.email_id, status="imported", opportunity_id=selected.opportunity_id)
        imported += 1
    return {"imported": imported, "items": db.list_email_messages()}


# --- legacy local profile / experience bank ---
@app.get("/api/profile")
async def get_profile():
    return {"profile": db.get_profile()}


@app.patch("/api/profile")
async def patch_profile(payload: ProfilePatch):
    return {"profile": db.update_profile(payload.model_dump(exclude_unset=True))}


@app.post("/api/profile/photo")
async def upload_profile_photo(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="证件照仅支持 JPG、PNG 或 WEBP 图片")
    content = await file.read()
    if not content or len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="证件照不能为空且不能超过 10MB")
    folder = db.DATA_DIR / "private" / "profile"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"id-photo{suffix}"
    path.write_bytes(content)
    profile = db.update_profile({"photo_path": str(path)})
    return {"profile": profile, "path": str(path)}


@app.get("/api/profile/photo")
async def profile_photo():
    photo = db.get_profile().get("photo_path")
    if not photo:
        raise HTTPException(status_code=404, detail="尚未上传证件照")
    private_root = (db.DATA_DIR / "private" / "profile").resolve()
    path = Path(str(photo)).resolve()
    if private_root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="证件照不存在")
    media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(path, media_type=media_type)


@app.get("/api/experiences")
async def experiences():
    return {"items": db.list_experiences()}


@app.post("/api/experiences")
async def create_experience(payload: ExperiencePayload):
    if payload.category not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="未知经历类型")
    item = payload.model_dump()
    item["source"] = "manual"
    return {"item": db.insert_experience(item)}


@app.patch("/api/experiences/{experience_id}")
async def patch_experience(experience_id: int, payload: ExperiencePatch):
    fields = payload.model_dump(exclude_unset=True)
    if "category" in fields and fields["category"] not in ALLOWED_CATEGORIES:
        raise HTTPException(status_code=400, detail="未知经历类型")
    item = db.update_experience(experience_id, fields)
    if not item:
        raise HTTPException(status_code=404, detail="经历不存在")
    return {"item": item}


@app.delete("/api/experiences/{experience_id}")
async def delete_experience(experience_id: int):
    if not db.delete_experience(experience_id):
        raise HTTPException(status_code=404, detail="经历不存在")
    return {"ok": True}


@app.post("/api/resume/import")
async def import_resume(file: UploadFile = File(...)):
    filename = file.filename or "resume"
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件过大，当前限制 15MB")
    try:
        text = extract_text_from_resume(filename, content)
        db.insert_resume_source(filename, Path(filename).suffix.lower(), text)
        parsed = await extract_resume_structured(text)
        profile_fields = {k: v for k, v in (parsed.get("profile") or {}).items() if k in db.PROFILE_FIELDS and str(v or "").strip()}
        if profile_fields:
            db.update_profile(profile_fields)
        created = db.replace_imported_experiences(parsed.get("experiences") or [], source=f"resume:{filename}")
        return {
            "profile": db.get_profile(), "experiences": created, "count": len(created),
            "mode": parsed.get("mode", "local"), "filename": filename,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"简历导入失败：{type(exc).__name__}: {exc}") from exc


# --- data safety / recovery ---
@app.get("/api/data/status")
async def data_status():
    return db.data_status()


@app.post("/api/data/backup")
async def create_backup():
    path = db.backup_database()
    if not path:
        raise HTTPException(status_code=500, detail="备份失败")
    return {"ok": True, "path": path, "status": db.data_status()}


@app.post("/api/data/merge-db")
async def merge_old_db(file: UploadFile = File(...)):
    if not (file.filename or "").lower().endswith((".db", ".sqlite", ".sqlite3")):
        raise HTTPException(status_code=422, detail="请选择旧版 jobpilot.db")
    content = await file.read()
    if len(content) > 250 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="数据库文件过大")
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        try:
            conn = sqlite3.connect(tmp_path)
            ok = conn.execute("PRAGMA integrity_check").fetchone()[0]
            conn.close()
            if ok != "ok":
                raise ValueError("数据库完整性检查失败")
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"不是可用的 SQLite 数据库：{exc}") from exc
        result = db.merge_legacy_database(tmp_path)
        return {"ok": True, "merged": result, "status": db.data_status()}
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


# --- CareerVault recommendation + tailored resume generation ---
@app.post("/api/careervault/recommendations")
async def careervault_recommendations(payload: CareerRecommendationRequest):
    target, _ = _resolve_target(payload.opportunity_id, payload.target_company, payload.target_role, payload.jd)
    cv = await careervault_all_resume_ready()
    if cv is None:
        raise HTTPException(status_code=503, detail="CareerVault 未连接。请先启动 CareerVault。")
    experiences = cv.get("experiences") or []
    if not experiences:
        raise HTTPException(status_code=400, detail="CareerVault 已连接，但没有 Resume Ready 经历。请先在 CareerVault 审核经历。")
    query = " ".join([target["target_company"], target["target_role"], target["target_jd"]]).strip()
    ranked = rank_experiences(experiences, query, default_count=6)
    local_profile = db.get_profile()
    profile = _merge_profile(local_profile, cv.get("profile") or {})
    return {
        "source": "careervault",
        "target": target,
        "profile": profile,
        "items": ranked,
        "count": len(ranked),
        "selected_default_ids": [str(x.get("id")) for x in ranked if x.get("selected_default")],
    }


@app.get("/api/resume-versions")
async def resume_versions():
    return {"items": db.list_resume_versions()}


@app.post("/api/resume/generate")
async def generate_resume(payload: ResumeGenerate):
    local_profile = db.get_profile()
    local_experiences = db.list_experiences()
    target, _ = _resolve_target(payload.opportunity_id, payload.target_company, payload.target_role, payload.jd)
    target_company, target_role, target_jd = target["target_company"], target["target_role"], target["target_jd"]

    source = "jobpilot-local-legacy"
    profile = local_profile
    experiences: list[dict[str, Any]] = []
    selection_mode = "legacy-explicit"

    # Explicit local IDs remain an intentional offline/recovery escape hatch.
    if payload.experience_ids:
        wanted = set(payload.experience_ids)
        experiences = [x for x in local_experiences if int(x["id"]) in wanted]
    elif payload.careervault_experience_ids is not None:
        # V0.3.1 human-reviewed CareerVault selection: exact IDs chosen in the UI.
        if not payload.careervault_experience_ids:
            raise HTTPException(status_code=400, detail="请至少选择一条 CareerVault 经历后再生成简历。")
        cv = await careervault_all_resume_ready()
        if cv is None:
            raise HTTPException(status_code=503, detail="CareerVault 未连接。请先启动 CareerVault。")
        source = "careervault"
        selection_mode = "careervault-human-reviewed"
        profile = _merge_profile(local_profile, cv.get("profile") or {})
        experiences = filter_selected(cv.get("experiences") or [], payload.careervault_experience_ids)
        missing = [x for x in payload.careervault_experience_ids if x not in {str(e.get("id")) for e in experiences}]
        if missing:
            raise HTTPException(status_code=409, detail=f"CareerVault 中有已选经历不可用或已取消 Resume Ready：{'、'.join(missing)}。请重新分析匹配。")
    else:
        # Backwards-compatible V0.3.0 automatic path for API clients that have not adopted selection UI yet.
        cv = await careervault_context(f"{target_company} {target_role} {target_jd}", limit=12)
        if cv is not None:
            source = "careervault"
            selection_mode = "careervault-auto"
            profile = _merge_profile(local_profile, cv.get("profile") or {})
            experiences = cv.get("experiences") or []
            if not experiences:
                raise HTTPException(
                    status_code=400,
                    detail="CareerVault 已连接，但没有可用于简历的 Resume Ready 经历。请先在 CareerVault 审核经历并开启 Resume Ready。",
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="CareerVault 未连接。请先启动 CareerVault；如需临时离线生成，可在 JobPilot 的旧经历区明确选择经历后再生成。",
            )

    if not experiences:
        raise HTTPException(status_code=400, detail="没有可用于生成简历的经历。")

    resume = await generate_tailored_resume(profile, experiences, target, None)
    resume["source"] = source
    resume["selection_mode"] = selection_mode
    resume["profile_snapshot"] = profile
    if source == "careervault":
        resume["selected_careervault_ids"] = [str(x.get("id")) for x in experiences]
    name = " · ".join(x for x in [target_company, target_role] if x) or "通用简历"
    version = db.insert_resume_version({
        "name": name,
        "target_opportunity_id": payload.opportunity_id,
        "target_company": target_company,
        "target_role": target_role,
        "target_jd": target_jd,
        "resume": resume,
        "autofill": resume.get("autofill", {}),
    })
    return {
        "item": version,
        "mode": resume.get("mode", "local"),
        "source": source,
        "selection_mode": selection_mode,
        "selected_careervault_ids": resume.get("selected_careervault_ids", []),
    }


@app.get("/api/resume-versions/{version_id}/docx")
async def download_resume_docx(version_id: int):
    version = db.get_resume_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="简历版本不存在")
    resume_payload = version.get("resume") or {}
    snapshot = resume_payload.get("profile_snapshot") if isinstance(resume_payload.get("profile_snapshot"), dict) else {}
    current = db.get_profile()
    # Keep the generated content stable, but always use the latest local photo.
    profile = {**snapshot, **{key: value for key, value in current.items() if value}}
    content = generate_docx_bytes(profile, version)
    parts = ["CareerOS", "简历", version.get("target_company"), version.get("target_role")]
    label = "_".join(str(item).strip() for item in parts if str(item or "").strip())
    label = re.sub(r'[\\/:*?"<>|]+', "_", label).strip(" ._") or "CareerOS_简历"
    ascii_name = f"CareerOS_Resume_{version_id}.docx"
    encoded_name = quote(f"{label}_{version_id}.docx")
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded_name}'},
    )


@app.get("/api/resume-versions/{version_id}/pdf")
async def download_resume_pdf(version_id: int):
    version = db.get_resume_version(version_id)
    if not version:
        raise HTTPException(status_code=404, detail="简历版本不存在")
    resume_payload = version.get("resume") or {}
    snapshot = resume_payload.get("profile_snapshot") if isinstance(resume_payload.get("profile_snapshot"), dict) else {}
    current = db.get_profile()
    profile = {**snapshot, **{key: value for key, value in current.items() if value}}
    try:
        content = generate_pdf_bytes(profile, version)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    label = "_".join(str(item).strip() for item in ["CareerOS", "简历", version.get("target_company"), version.get("target_role")] if str(item or "").strip())
    label = re.sub(r'[\\/:*?"<>|]+', "_", label).strip(" ._") or "CareerOS_简历"
    encoded_name = quote(f"{label}_{version_id}.pdf")
    return Response(content=content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=CareerOS_Resume_{version_id}.pdf; filename*=UTF-8''{encoded_name}"})


@app.delete("/api/resume-versions/{version_id}")
async def delete_resume_version(version_id: int):
    if not db.delete_resume_version(version_id):
        raise HTTPException(status_code=404, detail="简历版本不存在")
    return {"ok": True}


@app.get("/api/interview-questions")
async def interview_questions(role_category: str = "", source_type: str = "", question_type: str = ""):
    return {"items": db.list_interview_questions(role_category=role_category, source_type=source_type, question_type=question_type)}


@app.post("/api/interview-questions")
async def create_interview_question(payload: InterviewQuestionPayload):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="请填写题目内容。")
    if payload.question_type not in {"written_test", "interview"}:
        raise HTTPException(status_code=400, detail="题目类型不正确。")
    if payload.source_type not in {"network", "personal"}:
        raise HTTPException(status_code=400, detail="题目来源不正确。")
    if payload.opportunity_id and not db.get_opportunity(payload.opportunity_id):
        raise HTTPException(status_code=404, detail="关联岗位不存在。")
    return {"item": db.save_interview_question(payload.model_dump())}


@app.patch("/api/interview-questions/{question_id}")
async def patch_interview_question(question_id: int, payload: InterviewQuestionPatch):
    current = db.get_interview_question(question_id)
    if not current:
        raise HTTPException(status_code=404, detail="题目不存在。")
    fields = payload.model_dump(exclude_unset=True)
    if "question" in fields and not str(fields["question"] or "").strip():
        raise HTTPException(status_code=400, detail="题目内容不能为空。")
    return {"item": db.save_interview_question(fields, question_id)}


@app.delete("/api/interview-questions/{question_id}")
async def remove_interview_question(question_id: int):
    if not db.delete_interview_question(question_id):
        raise HTTPException(status_code=404, detail="题目不存在。")
    return {"ok": True}


@app.get("/api/role-field-sets")
async def role_field_sets(role_category: str = ""):
    return {"items": db.list_role_field_sets(role_category)}


@app.post("/api/role-field-sets")
async def create_role_field_set(payload: RoleFieldSetPayload):
    if not payload.role_category.strip():
        raise HTTPException(status_code=400, detail="请填写岗位类别。")
    return {"item": db.save_role_field_set(payload.model_dump())}


@app.patch("/api/role-field-sets/{field_set_id}")
async def patch_role_field_set(field_set_id: int, payload: RoleFieldSetPatch):
    if not db.get_role_field_set(field_set_id):
        raise HTTPException(status_code=404, detail="常用字段不存在。")
    return {"item": db.save_role_field_set(payload.model_dump(exclude_unset=True), field_set_id)}


@app.delete("/api/role-field-sets/{field_set_id}")
async def remove_role_field_set(field_set_id: int):
    if not db.delete_role_field_set(field_set_id):
        raise HTTPException(status_code=404, detail="常用字段不存在。")
    return {"ok": True}


def _best_role_field_set(role: str) -> dict[str, Any] | None:
    role = str(role or "").strip().lower()
    if not role:
        return None
    candidates = []
    for item in db.list_role_field_sets():
        category = str(item.get("role_category") or "").strip().lower()
        if not category:
            continue
        score = 2 if category in role or role in category else 0
        if score:
            candidates.append((score, item))
    return max(candidates, key=lambda x: x[0])[1] if candidates else None


@app.get("/api/autofill/package")
async def autofill_package(opportunity_id: int | None = None):
    version = db.latest_resume_version(opportunity_id=opportunity_id)
    profile = db.get_profile()
    package = build_flat_package(version, profile)
    structured = build_structured_autofill(version, profile)
    role_field_set = _best_role_field_set(str((version or {}).get("target_role") or ""))
    if role_field_set:
        if role_field_set.get("self_evaluation"):
            package["self_intro"] = role_field_set["self_evaluation"]
        if role_field_set.get("skills"):
            package["skills"] = "、".join(role_field_set["skills"])
            structured["skills"] = role_field_set["skills"]
        structured["role_field_set"] = role_field_set
    return {
        "schema_version": 2,
        "package": package,
        "structured": structured,
        "role_field_set": role_field_set,
        "resume_version": version,
        "warning": "默认只填写普通文本/下拉字段与重复经历行；不会自动点击提交。身份证、政治面貌、民族等敏感字段需要在浏览器助手中单次明确允许，证件照文件仍需手动上传。",
    }
