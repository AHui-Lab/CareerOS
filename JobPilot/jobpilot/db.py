from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
LEGACY_DATA_DIR = ROOT / "data"

def _default_data_dir() -> Path:
    custom = os.getenv("JOBPILOT_DATA_DIR", "").strip()
    if custom:
        return Path(custom).expanduser().resolve()
    if os.name == "nt":
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / "JobPilot"
    if sys_platform := os.getenv("XDG_DATA_HOME", "").strip():
        return Path(sys_platform).expanduser() / "jobpilot"
    return Path.home() / ".local" / "share" / "jobpilot"

DATA_DIR = _default_data_dir()
DB_PATH = DATA_DIR / "jobpilot.db"
BACKUP_DIR = DATA_DIR / "backups"

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'url',
    title TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    deadline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    raw_text TEXT NOT NULL DEFAULT '',
    note TEXT NOT NULL DEFAULT '',
    match_score INTEGER NOT NULL DEFAULT 0,
    match_reasons TEXT NOT NULL DEFAULT '[]',
    risks TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'inbox',
    page_kind TEXT NOT NULL DEFAULT 'unknown',
    adapter_name TEXT NOT NULL DEFAULT '通用网页',
    page_context TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
CREATE INDEX IF NOT EXISTS idx_opportunities_created_at ON opportunities(created_at DESC);

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    birth_date TEXT NOT NULL DEFAULT '',
    current_city TEXT NOT NULL DEFAULT '',
    school TEXT NOT NULL DEFAULT '',
    college TEXT NOT NULL DEFAULT '',
    major TEXT NOT NULL DEFAULT '',
    degree TEXT NOT NULL DEFAULT '',
    graduation_date TEXT NOT NULL DEFAULT '',
    gpa TEXT NOT NULL DEFAULT '',
    rank TEXT NOT NULL DEFAULT '',
    website TEXT NOT NULL DEFAULT '',
    portfolio_url TEXT NOT NULL DEFAULT '',
    github_url TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT OR IGNORE INTO profile(id) VALUES (1);

CREATE TABLE IF NOT EXISTS experiences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL DEFAULT 'other',
    title TEXT NOT NULL DEFAULT '',
    organization TEXT NOT NULL DEFAULT '',
    start_date TEXT NOT NULL DEFAULT '',
    end_date TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    highlights TEXT NOT NULL DEFAULT '[]',
    tags TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_experiences_category ON experiences(category);
CREATE INDEX IF NOT EXISTS idx_experiences_created_at ON experiences(created_at DESC);

CREATE TABLE IF NOT EXISTS resume_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL DEFAULT '',
    file_type TEXT NOT NULL DEFAULT '',
    extracted_text TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS resume_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL DEFAULT '',
    target_opportunity_id INTEGER,
    target_company TEXT NOT NULL DEFAULT '',
    target_role TEXT NOT NULL DEFAULT '',
    target_jd TEXT NOT NULL DEFAULT '',
    resume_json TEXT NOT NULL DEFAULT '{}',
    autofill_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(target_opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_resume_versions_created_at ON resume_versions(created_at DESC);

CREATE TABLE IF NOT EXISTS vault_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vault_name TEXT NOT NULL DEFAULT '',
    relative_path TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    content_hash TEXT NOT NULL DEFAULT '',
    source_type TEXT NOT NULL DEFAULT 'obsidian',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(vault_name, relative_path)
);
CREATE INDEX IF NOT EXISTS idx_vault_documents_title ON vault_documents(title);
CREATE INDEX IF NOT EXISTS idx_vault_documents_updated_at ON vault_documents(updated_at DESC);
"""


def _copy_legacy_database_if_needed() -> bool:
    """Move V0.2.0-and-earlier project-local data into the stable user data directory once."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    legacy_db = LEGACY_DATA_DIR / "jobpilot.db"
    if DB_PATH.exists() or not legacy_db.exists() or legacy_db.resolve() == DB_PATH.resolve():
        return False
    try:
        shutil.copy2(legacy_db, DB_PATH)
        return True
    except OSError:
        return False


def backup_database(*, keep: int = 12) -> str | None:
    if not DB_PATH.exists() or DB_PATH.stat().st_size <= 0:
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"jobpilot-{stamp}.db"
    try:
        source = sqlite3.connect(DB_PATH)
        dest = sqlite3.connect(target)
        try:
            source.backup(dest)
        finally:
            dest.close(); source.close()
        backups = sorted(BACKUP_DIR.glob("jobpilot-*.db"), key=lambda x: x.stat().st_mtime, reverse=True)
        for old in backups[max(1, keep):]:
            try:
                old.unlink()
            except OSError:
                pass
        return str(target)
    except Exception:
        return None


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    migrated = _copy_legacy_database_if_needed()
    existed = DB_PATH.exists() and DB_PATH.stat().st_size > 0
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(opportunities)").fetchall()}
        migrations = {
            "page_kind": "ALTER TABLE opportunities ADD COLUMN page_kind TEXT NOT NULL DEFAULT 'unknown'",
            "adapter_name": "ALTER TABLE opportunities ADD COLUMN adapter_name TEXT NOT NULL DEFAULT '通用网页'",
            "page_context": "ALTER TABLE opportunities ADD COLUMN page_context TEXT NOT NULL DEFAULT '{}'",
            "note": "ALTER TABLE opportunities ADD COLUMN note TEXT NOT NULL DEFAULT ''",
        }
        for column, sql in migrations.items():
            if column not in columns:
                conn.execute(sql)
    # On version upgrades make a safety snapshot after migrations. Keep this best-effort.
    if existed or migrated:
        backup_database()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _loads(value: Any, default: Any) -> Any:
    try:
        return json.loads(value or json.dumps(default, ensure_ascii=False))
    except (json.JSONDecodeError, TypeError):
        return default


def _opportunity_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["match_reasons"] = _loads(result.get("match_reasons"), [])
    result["risks"] = _loads(result.get("risks"), [])
    result["page_context"] = _loads(result.get("page_context"), {})
    return result


def _experience_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["highlights"] = _loads(result.get("highlights"), [])
    result["tags"] = _loads(result.get("tags"), [])
    return result


def _resume_version_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["resume"] = _loads(result.pop("resume_json", "{}"), {})
    result["autofill"] = _loads(result.pop("autofill_json", "{}"), {})
    return result


# --- opportunities / memo ---

def list_opportunities() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM opportunities ORDER BY created_at DESC, id DESC").fetchall()
    return [_opportunity_row(row) for row in rows]


def get_opportunity(opportunity_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
    return _opportunity_row(row) if row else None


def find_by_url(source_url: str) -> dict[str, Any] | None:
    if not source_url:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM opportunities WHERE source_url = ? ORDER BY id DESC LIMIT 1", (source_url,)
        ).fetchone()
    return _opportunity_row(row) if row else None


def _serialized_opportunity(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload["match_reasons"] = json.dumps(payload.get("match_reasons", []), ensure_ascii=False)
    payload["risks"] = json.dumps(payload.get("risks", []), ensure_ascii=False)
    payload["page_context"] = json.dumps(payload.get("page_context", {}), ensure_ascii=False)
    return payload


def insert_opportunity(item: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "source_url", "source_type", "title", "company", "role", "location", "deadline",
        "description", "raw_text", "note", "match_score", "match_reasons", "risks", "status",
        "page_kind", "adapter_name", "page_context"
    )
    payload = _serialized_opportunity(item)
    values = [payload.get(field, "") for field in fields]
    with connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO opportunities ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", values
        )
        new_id = int(cursor.lastrowid)
    return get_opportunity(new_id) or {}


def refresh_opportunity(opportunity_id: int, item: dict[str, Any], *, preserve_status: bool = True) -> dict[str, Any] | None:
    current = get_opportunity(opportunity_id)
    if not current:
        return None
    payload = _serialized_opportunity(item)
    fields = [
        "source_url", "source_type", "title", "company", "role", "location", "deadline", "description",
        "raw_text", "match_score", "match_reasons", "risks", "page_kind", "adapter_name", "page_context"
    ]
    if not preserve_status:
        fields.append("status")
    values = [payload.get(field, current.get(field, "")) for field in fields] + [opportunity_id]
    with connect() as conn:
        conn.execute(
            f"UPDATE opportunities SET {', '.join(f'{field} = ?' for field in fields)}, updated_at = datetime('now', 'localtime') WHERE id = ?",
            values,
        )
    return get_opportunity(opportunity_id)


def edit_opportunity(opportunity_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    allowed = {"company", "role", "location", "deadline", "note"}
    clean = {key: str(value or "").strip() for key, value in fields.items() if key in allowed}
    if not clean:
        return get_opportunity(opportunity_id)
    with connect() as conn:
        conn.execute(
            f"UPDATE opportunities SET {', '.join(f'{field} = ?' for field in clean)}, updated_at = datetime('now', 'localtime') WHERE id = ?",
            [*clean.values(), opportunity_id],
        )
    return get_opportunity(opportunity_id)


def update_status(opportunity_id: int, status: str) -> dict[str, Any] | None:
    with connect() as conn:
        conn.execute(
            "UPDATE opportunities SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
            (status, opportunity_id),
        )
    return get_opportunity(opportunity_id)


def delete_opportunity(opportunity_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM opportunities WHERE id = ?", (opportunity_id,))
        return cursor.rowcount > 0


# --- profile ---
PROFILE_FIELDS = {
    "name", "phone", "email", "gender", "birth_date", "current_city", "school", "college", "major", "degree",
    "graduation_date", "gpa", "rank", "website", "portfolio_url", "github_url", "summary"
}


def get_profile() -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(row) if row else {"id": 1}


def update_profile(fields: dict[str, Any]) -> dict[str, Any]:
    clean = {key: str(value or "").strip() for key, value in fields.items() if key in PROFILE_FIELDS}
    if clean:
        with connect() as conn:
            conn.execute(
                f"UPDATE profile SET {', '.join(f'{field} = ?' for field in clean)}, updated_at = datetime('now', 'localtime') WHERE id = 1",
                [*clean.values()],
            )
    return get_profile()


# --- experiences ---
EXPERIENCE_FIELDS = {
    "category", "title", "organization", "start_date", "end_date", "location", "description", "highlights", "tags", "source"
}


def list_experiences() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM experiences ORDER BY created_at DESC, id DESC").fetchall()
    return [_experience_row(row) for row in rows]


def get_experience(experience_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM experiences WHERE id = ?", (experience_id,)).fetchone()
    return _experience_row(row) if row else None


def insert_experience(item: dict[str, Any]) -> dict[str, Any]:
    fields = ["category", "title", "organization", "start_date", "end_date", "location", "description", "highlights", "tags", "source"]
    payload = dict(item)
    payload["highlights"] = json.dumps(payload.get("highlights", []), ensure_ascii=False)
    payload["tags"] = json.dumps(payload.get("tags", []), ensure_ascii=False)
    values = [payload.get(field, "") for field in fields]
    with connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO experiences ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", values
        )
        new_id = int(cursor.lastrowid)
    return get_experience(new_id) or {}


def update_experience(experience_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not get_experience(experience_id):
        return None
    clean: dict[str, Any] = {}
    for key, value in fields.items():
        if key not in EXPERIENCE_FIELDS:
            continue
        if key in {"highlights", "tags"}:
            clean[key] = json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)
        else:
            clean[key] = str(value or "").strip()
    if clean:
        with connect() as conn:
            conn.execute(
                f"UPDATE experiences SET {', '.join(f'{field} = ?' for field in clean)}, updated_at = datetime('now', 'localtime') WHERE id = ?",
                [*clean.values(), experience_id],
            )
    return get_experience(experience_id)


def delete_experience(experience_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM experiences WHERE id = ?", (experience_id,))
        return cursor.rowcount > 0


def replace_imported_experiences(items: list[dict[str, Any]], *, source: str) -> list[dict[str, Any]]:
    created = []
    for item in items:
        payload = dict(item)
        payload["source"] = source
        created.append(insert_experience(payload))
    return created


# --- resume source files ---

def insert_resume_source(filename: str, file_type: str, extracted_text: str) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO resume_sources(filename, file_type, extracted_text) VALUES (?, ?, ?)",
            (filename, file_type, extracted_text),
        )
        return int(cursor.lastrowid)


# --- generated resumes ---

def insert_resume_version(item: dict[str, Any]) -> dict[str, Any]:
    fields = ["name", "target_opportunity_id", "target_company", "target_role", "target_jd", "resume_json", "autofill_json"]
    payload = {
        "name": item.get("name", ""),
        "target_opportunity_id": item.get("target_opportunity_id"),
        "target_company": item.get("target_company", ""),
        "target_role": item.get("target_role", ""),
        "target_jd": item.get("target_jd", ""),
        "resume_json": json.dumps(item.get("resume", {}), ensure_ascii=False),
        "autofill_json": json.dumps(item.get("autofill", {}), ensure_ascii=False),
    }
    with connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO resume_versions ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
            [payload[field] for field in fields],
        )
        new_id = int(cursor.lastrowid)
    return get_resume_version(new_id) or {}


def get_resume_version(version_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM resume_versions WHERE id = ?", (version_id,)).fetchone()
    return _resume_version_row(row) if row else None


def list_resume_versions(limit: int = 30) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM resume_versions ORDER BY created_at DESC, id DESC LIMIT ?", (max(1, min(limit, 100)),)
        ).fetchall()
    return [_resume_version_row(row) for row in rows]


def latest_resume_version(*, opportunity_id: int | None = None) -> dict[str, Any] | None:
    with connect() as conn:
        if opportunity_id:
            row = conn.execute(
                "SELECT * FROM resume_versions WHERE target_opportunity_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
                (opportunity_id,),
            ).fetchone()
            if row:
                return _resume_version_row(row)
        row = conn.execute("SELECT * FROM resume_versions ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
    return _resume_version_row(row) if row else None

# --- Obsidian / knowledge vault ---

def _vault_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["tags"] = _loads(result.get("tags"), [])
    return result


def upsert_vault_document(item: dict[str, Any]) -> dict[str, Any]:
    vault_name = str(item.get("vault_name") or "Obsidian").strip() or "Obsidian"
    relative_path = str(item.get("relative_path") or item.get("title") or "note.md").replace("\\", "/").strip("/")
    content = str(item.get("content") or "")
    title = str(item.get("title") or Path(relative_path).stem).strip()
    tags = item.get("tags") if isinstance(item.get("tags"), list) else []
    digest = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, content_hash FROM vault_documents WHERE vault_name = ? AND relative_path = ?",
            (vault_name, relative_path),
        ).fetchone()
        if row:
            if row["content_hash"] != digest:
                conn.execute(
                    "UPDATE vault_documents SET title=?, content=?, tags=?, content_hash=?, source_type=?, updated_at=datetime('now','localtime') WHERE id=?",
                    (title, content, json.dumps(tags, ensure_ascii=False), digest, str(item.get("source_type") or "obsidian"), row["id"]),
                )
            doc_id = int(row["id"])
        else:
            cur = conn.execute(
                "INSERT INTO vault_documents(vault_name,relative_path,title,content,tags,content_hash,source_type) VALUES(?,?,?,?,?,?,?)",
                (vault_name, relative_path, title, content, json.dumps(tags, ensure_ascii=False), digest, str(item.get("source_type") or "obsidian")),
            )
            doc_id = int(cur.lastrowid)
    return get_vault_document(doc_id) or {}


def get_vault_document(document_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM vault_documents WHERE id=?", (document_id,)).fetchone()
    return _vault_row(row) if row else None


def list_vault_documents(limit: int = 100) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id,vault_name,relative_path,title,tags,source_type,created_at,updated_at,length(content) AS content_length FROM vault_documents ORDER BY updated_at DESC,id DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()
    result=[]
    for row in rows:
        item=dict(row); item["tags"]=_loads(item.get("tags"),[]); result.append(item)
    return result


def count_vault_documents() -> int:
    with connect() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM vault_documents").fetchone()[0])


def search_vault_documents(query: str, limit: int = 12) -> list[dict[str, Any]]:
    import re
    tokens = [x.lower() for x in re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{1,30}|[\u4e00-\u9fff]{2,10}", query or "") if len(x) >= 2]
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vault_documents ORDER BY updated_at DESC,id DESC LIMIT 1000").fetchall()
    scored=[]
    for row in rows:
        item=_vault_row(row)
        hay=(f"{item.get('relative_path','')} {item.get('title','')} {item.get('content','')} {' '.join(item.get('tags') or [])}").lower()
        score=sum((4 if t in str(item.get('title','')).lower() else 1) for t in tokens if t in hay)
        path=str(item.get('relative_path','')).lower()
        if any(k in path for k in ["简历","resume","cv","经历","项目","实习","科研","获奖"]): score += 2
        scored.append((score, int(item.get('id') or 0), item))
    scored.sort(key=lambda x:(x[0],x[1]), reverse=True)
    chosen=[item for score,_,item in scored if score>0][:limit]
    if not chosen:
        chosen=[item for _,_,item in scored[:min(limit,6)]]
    for item in chosen:
        item["content"] = str(item.get("content") or "")[:12000]
    return chosen


def data_status() -> dict[str, Any]:
    with connect() as conn:
        counts = {
            "opportunities": int(conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]),
            "experiences": int(conn.execute("SELECT COUNT(*) FROM experiences").fetchone()[0]),
            "resume_versions": int(conn.execute("SELECT COUNT(*) FROM resume_versions").fetchone()[0]),
            "vault_documents": int(conn.execute("SELECT COUNT(*) FROM vault_documents").fetchone()[0]),
        }
    backups = sorted(BACKUP_DIR.glob("jobpilot-*.db"), key=lambda x: x.stat().st_mtime, reverse=True) if BACKUP_DIR.exists() else []
    return {"db_path": str(DB_PATH), "backup_dir": str(BACKUP_DIR), "backup_count": len(backups), "latest_backup": str(backups[0]) if backups else "", **counts}


def merge_legacy_database(old_path: Path) -> dict[str, int]:
    """Merge an older JobPilot sqlite DB without overwriting newer/current records."""
    result={"opportunities":0,"experiences":0,"resume_versions":0,"profile_fields":0}
    old=sqlite3.connect(old_path); old.row_factory=sqlite3.Row
    try:
        tables={r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "opportunities" in tables:
            cols={r[1] for r in old.execute("PRAGMA table_info(opportunities)").fetchall()}
            for r in old.execute("SELECT * FROM opportunities ORDER BY id"):
                d=dict(r)
                url=str(d.get("source_url") or "")
                if url and find_by_url(url): continue
                # Avoid obvious duplicates without URLs.
                with connect() as conn:
                    duplicate=conn.execute("SELECT id FROM opportunities WHERE company=? AND role=? AND title=? LIMIT 1", (str(d.get('company') or ''),str(d.get('role') or ''),str(d.get('title') or ''))).fetchone()
                if duplicate: continue
                item={
                    "source_url":url,"source_type":d.get("source_type","legacy"),"title":d.get("title",""),"company":d.get("company",""),"role":d.get("role",""),
                    "location":d.get("location",""),"deadline":d.get("deadline",""),"description":d.get("description",""),"raw_text":d.get("raw_text",""),"note":d.get("note","") if "note" in cols else "",
                    "match_score":d.get("match_score",0),"match_reasons":_loads(d.get("match_reasons"),[]),"risks":_loads(d.get("risks"),[]),"status":d.get("status","inbox"),
                    "page_kind":d.get("page_kind","unknown") if "page_kind" in cols else "unknown", "adapter_name":d.get("adapter_name","旧版") if "adapter_name" in cols else "旧版",
                    "page_context":_loads(d.get("page_context"),{}) if "page_context" in cols else {},
                }
                insert_opportunity(item); result["opportunities"]+=1
        if "profile" in tables:
            row=old.execute("SELECT * FROM profile WHERE id=1").fetchone()
            if row:
                current=get_profile(); patch={}
                for k,v in dict(row).items():
                    if k in PROFILE_FIELDS and not str(current.get(k) or '').strip() and str(v or '').strip(): patch[k]=v
                if patch:
                    update_profile(patch); result["profile_fields"]=len(patch)
        if "experiences" in tables:
            oldcols={r[1] for r in old.execute("PRAGMA table_info(experiences)").fetchall()}
            for r in old.execute("SELECT * FROM experiences ORDER BY id"):
                d=dict(r)
                sig=(str(d.get('category') or ''),str(d.get('title') or ''),str(d.get('organization') or ''),str(d.get('start_date') or ''),str(d.get('description') or ''))
                with connect() as conn:
                    dup=conn.execute("SELECT id FROM experiences WHERE category=? AND title=? AND organization=? AND start_date=? AND description=? LIMIT 1", sig).fetchone()
                if dup: continue
                insert_experience({k:d.get(k, [] if k in {'highlights','tags'} else '') for k in EXPERIENCE_FIELDS if k != 'source'} | {"highlights":_loads(d.get('highlights'),[]),"tags":_loads(d.get('tags'),[]),"source":"legacy-db"})
                result["experiences"]+=1
    finally:
        old.close()
    backup_database()
    return result

