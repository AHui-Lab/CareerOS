from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
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
    note: str | None = Field(default=None, max_length=4000)


class ProfilePatch(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    gender: str | None = None
    birth_date: str | None = None
    current_city: str | None = None
    school: str | None = None
    college: str | None = None
    major: str | None = None
    degree: str | None = None
    graduation_date: str | None = None
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


# --- legacy local profile / experience bank ---
@app.get("/api/profile")
async def get_profile():
    return {"profile": db.get_profile()}


@app.patch("/api/profile")
async def patch_profile(payload: ProfilePatch):
    return {"profile": db.update_profile(payload.model_dump(exclude_unset=True))}


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
    profile = resume_payload.get("profile_snapshot") if isinstance(resume_payload.get("profile_snapshot"), dict) else db.get_profile()
    content = generate_docx_bytes(profile, version)
    safe = "JobPilot_Resume"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{safe}_{version_id}.docx"'},
    )


@app.get("/api/autofill/package")
async def autofill_package(opportunity_id: int | None = None):
    version = db.latest_resume_version(opportunity_id=opportunity_id)
    profile = db.get_profile()
    package = build_flat_package(version, profile)
    structured = build_structured_autofill(version, profile)
    return {
        "schema_version": 2,
        "package": package,
        "structured": structured,
        "resume_version": version,
        "warning": "只用于填写安全的文本/下拉字段与重复经历行；不会自动点击提交，也不会自动处理薪资、家庭、政治面貌、健康等需要本人判断的问题。",
    }
