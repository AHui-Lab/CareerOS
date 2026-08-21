from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
VAULT = ROOT / "vault"
PRIVATE = ROOT / "private"
EXPERIENCES = VAULT / "experiences"
INBOX = VAULT / "inbox"
PROFILE = VAULT / "profile"
APPLICATIONS = VAULT / "applications"
GENERATED = VAULT / "generated"
SETTINGS = ROOT / "config" / "settings.yaml"
TEXT_EXTS = {".md", ".txt", ".yaml", ".yml", ".json"}

for path in (VAULT, PRIVATE, EXPERIENCES, INBOX, PROFILE, APPLICATIONS, GENERATED):
    path.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def today() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        value = "experience"
    return value[:70]


def atomic_write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if isinstance(content, bytes) else "w"
    kwargs = {} if isinstance(content, bytes) else {"encoding": "utf-8", "newline": "\n"}
    with tempfile.NamedTemporaryFile(mode=mode, delete=False, dir=path.parent, **kwargs) as handle:
        handle.write(content)
        temp_name = handle.name
    os.replace(temp_name, path)


def split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if text.startswith("---\n"):
        match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, flags=re.S)
        if match:
            return yaml.safe_load(match.group(1)) or {}, match.group(2)
    return {}, text


def dump_frontmatter(meta: dict[str, Any], body: str) -> str:
    yaml_text = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{yaml_text}\n---\n\n{body.rstrip()}\n"


def section(body: str, heading: str) -> str:
    pattern = rf"(?ms)^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, body)
    return match.group(1).strip() if match else ""


def render_experience(meta: dict[str, Any], fields: dict[str, Any]) -> str:
    title = fields.get("title") or meta.get("title") or "未命名经历"
    sections = [
        f"# {title}",
        "",
        "## 项目概述",
        fields.get("summary", "").strip(),
        "",
        "## 事实记录",
        fields.get("facts", "").strip(),
        "",
        "## 量化成果",
        fields.get("results", "").strip(),
        "",
        "## Notes",
        fields.get("notes", "").strip(),
        "",
    ]
    return "\n".join(sections).strip() + "\n"


def experience_to_dict(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)
    return {
        **meta,
        "summary": section(body, "项目概述"),
        "facts": section(body, "事实记录"),
        "results": section(body, "量化成果"),
        "notes": section(body, "Notes"),
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "attachments": list_attachments(meta.get("id", path.parent.name)),
    }


def list_experiences() -> list[dict[str, Any]]:
    items = []
    for path in EXPERIENCES.glob("*/index.md"):
        try:
            items.append(experience_to_dict(path))
        except Exception as exc:
            items.append({"id": path.parent.name, "title": path.parent.name, "error": str(exc)})
    return sorted(items, key=lambda x: x.get("updated_at", ""), reverse=True)


def get_experience(experience_id: str) -> dict[str, Any]:
    path = EXPERIENCES / experience_id / "index.md"
    if not path.exists():
        raise FileNotFoundError(experience_id)
    return experience_to_dict(path)


def create_experience(payload: dict[str, Any]) -> dict[str, Any]:
    base = slugify(payload.get("title", "experience"))
    candidate = base
    i = 2
    while (EXPERIENCES / candidate).exists():
        candidate = f"{base}-{i}"
        i += 1
    experience_id = candidate
    ts = now_iso()
    meta = {
        "schema_version": 1,
        "id": experience_id,
        "type": payload.get("type", "project"),
        "title": payload.get("title", ""),
        "organization": payload.get("organization", ""),
        "role": payload.get("role", ""),
        "start": payload.get("start", ""),
        "end": payload.get("end", ""),
        "status": payload.get("status", "active"),
        "domains": payload.get("domains", []),
        "skills": payload.get("skills", []),
        "resume_ready": bool(payload.get("resume_ready", False)),
        "created_at": ts,
        "updated_at": ts,
    }
    body = render_experience(meta, payload)
    path = EXPERIENCES / experience_id / "index.md"
    atomic_write(path, dump_frontmatter(meta, body))
    return get_experience(experience_id)


def update_experience(experience_id: str, changes: dict[str, Any]) -> dict[str, Any]:
    current = get_experience(experience_id)
    path = EXPERIENCES / experience_id / "index.md"
    meta_keys = {"type", "title", "organization", "role", "start", "end", "status", "domains", "skills", "resume_ready"}
    body_keys = {"summary", "facts", "results", "notes"}
    meta = {k: current.get(k) for k in current.keys() if k not in body_keys and k not in {"path", "attachments", "error"}}
    for key, value in changes.items():
        if key in meta_keys and value is not None:
            meta[key] = value
    meta["updated_at"] = now_iso()
    fields = {k: current.get(k, "") for k in body_keys}
    for key, value in changes.items():
        if key in body_keys and value is not None:
            fields[key] = value
    body = render_experience(meta, {**fields, "title": meta.get("title", "")})
    atomic_write(path, dump_frontmatter(meta, body))
    return get_experience(experience_id)


def delete_experience(experience_id: str) -> None:
    path = EXPERIENCES / experience_id
    if not path.exists():
        raise FileNotFoundError(experience_id)
    shutil.rmtree(path)


def list_attachments(experience_id: str) -> list[dict[str, Any]]:
    folder = EXPERIENCES / experience_id / "attachments"
    if not folder.exists():
        return []
    out = []
    for path in sorted(folder.iterdir()):
        if path.is_file():
            out.append({"name": path.name, "size": path.stat().st_size, "path": str(path.relative_to(ROOT)).replace("\\", "/")})
    return out


def save_attachment(experience_id: str, filename: str, data: bytes) -> dict[str, Any]:
    if not (EXPERIENCES / experience_id / "index.md").exists():
        raise FileNotFoundError(experience_id)
    safe = Path(filename).name
    folder = EXPERIENCES / experience_id / "attachments"
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / safe
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        n = 2
        while dest.exists():
            dest = folder / f"{stem}-{n}{suffix}"
            n += 1
    atomic_write(dest, data)
    return {"name": dest.name, "size": len(data), "path": str(dest.relative_to(ROOT)).replace("\\", "/")}


def add_inbox(payload: dict[str, Any]) -> dict[str, Any]:
    ts = now_iso()
    item_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    title = payload.get("title") or payload.get("content", "")[:40].replace("\n", " ")
    meta = {
        "schema_version": 1,
        "id": item_id,
        "type": "inbox",
        "kind": payload.get("kind", "note"),
        "title": title,
        "related_experience_id": payload.get("related_experience_id", ""),
        "created_at": ts,
    }
    body = f"# {title}\n\n{payload.get('content', '').strip()}\n"
    path = INBOX / f"{item_id}.md"
    atomic_write(path, dump_frontmatter(meta, body))
    return {**meta, "content": payload.get("content", ""), "path": str(path.relative_to(ROOT)).replace("\\", "/")}


def list_inbox() -> list[dict[str, Any]]:
    items = []
    for path in INBOX.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        meta, body = split_frontmatter(text)
        content = re.sub(r"^# .*?\n+", "", body, count=1).strip()
        items.append({**meta, "content": content, "path": str(path.relative_to(ROOT)).replace("\\", "/")})
    return sorted(items, key=lambda x: x.get("created_at", ""), reverse=True)


def delete_inbox(item_id: str) -> None:
    path = INBOX / f"{item_id}.md"
    if not path.exists():
        raise FileNotFoundError(item_id)
    path.unlink()


def get_profile() -> dict[str, Any]:
    public_path = PROFILE / "public.yaml"
    private_path = PRIVATE / "profile.yaml"
    public = yaml.safe_load(public_path.read_text(encoding="utf-8")) if public_path.exists() else {}
    private = yaml.safe_load(private_path.read_text(encoding="utf-8")) if private_path.exists() else {}
    return {**(public or {}), **(private or {})}


def update_profile(payload: dict[str, Any]) -> dict[str, Any]:
    public_keys = {"name", "city", "headline", "github", "portfolio", "education", "skills"}
    private_keys = {"email", "phone"}
    current = get_profile()
    merged = {**current, **payload, "updated_at": now_iso()}
    public = {k: merged.get(k, [] if k in {"education", "skills"} else "") for k in public_keys}
    public["updated_at"] = merged["updated_at"]
    private = {k: merged.get(k, "") for k in private_keys}
    private["updated_at"] = merged["updated_at"]
    atomic_write(PROFILE / "public.yaml", yaml.safe_dump(public, allow_unicode=True, sort_keys=False))
    atomic_write(PRIVATE / "profile.yaml", yaml.safe_dump(private, allow_unicode=True, sort_keys=False))
    return get_profile()


def load_settings() -> dict[str, Any]:
    if not SETTINGS.exists():
        return {"git_data_snapshots_enabled": False}
    try:
        data = yaml.safe_load(SETTINGS.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"git_data_snapshots_enabled": False}


def safe_vault_path(relative_path: str) -> Path:
    raw = str(relative_path or "").replace("\\", "/").strip().lstrip("/")
    if not raw:
        raise ValueError("path is required")
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("unsafe path")
    root = VAULT.resolve()
    path = (VAULT / rel).resolve()
    if path != root and root not in path.parents:
        raise ValueError("path escapes vault")
    return path


def list_files() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not VAULT.exists():
        return items
    for path in VAULT.rglob("*"):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        rel = str(path.relative_to(VAULT)).replace("\\", "/")
        ext = path.suffix.lower()
        items.append({
            "path": rel,
            "name": path.name,
            "size": path.stat().st_size,
            "text_editable": ext in TEXT_EXTS,
            "extension": ext,
            "updated_at": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        })
    return sorted(items, key=lambda x: x.get("updated_at", ""), reverse=True)


def read_text_file(relative_path: str) -> dict[str, Any]:
    path = safe_vault_path(relative_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(relative_path)
    if path.suffix.lower() not in TEXT_EXTS:
        raise ValueError("file is not text-editable")
    if path.stat().st_size > 2 * 1024 * 1024:
        raise ValueError("text file is too large to edit in browser")
    return {"path": str(path.relative_to(VAULT)).replace("\\", "/"), "content": path.read_text(encoding="utf-8")}


def write_text_file(relative_path: str, content: str) -> dict[str, Any]:
    path = safe_vault_path(relative_path)
    if path.suffix.lower() not in TEXT_EXTS:
        raise ValueError("file is not text-editable")
    if len(content.encode("utf-8")) > 2 * 1024 * 1024:
        raise ValueError("text file is too large to edit in browser")
    atomic_write(path, content)
    return {"ok": True, "path": str(path.relative_to(VAULT)).replace("\\", "/"), "size": path.stat().st_size}


def save_vault_upload(filename: str, data: bytes, directory: str = "inbox/files") -> dict[str, Any]:
    safe_name = Path(filename).name or "upload.bin"
    folder = safe_vault_path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    dest = folder / safe_name
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        n = 2
        while dest.exists():
            dest = folder / f"{stem}-{n}{suffix}"
            n += 1
    atomic_write(dest, data)
    return {"name": dest.name, "size": len(data), "path": str(dest.relative_to(VAULT)).replace("\\", "/")}


def tokenize(text: str) -> set[str]:
    english = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", text.lower())
    chinese = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    chars = []
    for chunk in chinese:
        chars.extend(chunk[i:i+2] for i in range(max(0, len(chunk)-1)))
    return set(english + chars)


def rank_experiences(query: str, only_resume_ready: bool = True) -> list[dict[str, Any]]:
    q = tokenize(query)
    ranked = []
    for item in list_experiences():
        if only_resume_ready and not item.get("resume_ready"):
            continue
        hay = " ".join(str(item.get(k, "")) for k in ("title", "organization", "role", "domains", "skills", "summary", "facts", "results"))
        tokens = tokenize(hay)
        overlap = len(q & tokens)
        score = overlap / max(1, len(q)) if q else 0
        copy = dict(item)
        copy["match_score"] = round(score, 4)
        ranked.append(copy)
    return sorted(ranked, key=lambda x: (x["match_score"], x.get("updated_at", "")), reverse=True)


def git_status() -> dict[str, Any]:
    try:
        proc = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, timeout=5)
        return {"available": proc.returncode == 0, "changes": [line for line in proc.stdout.splitlines() if line.strip()], "error": proc.stderr.strip()}
    except Exception as exc:
        return {"available": False, "changes": [], "error": str(exc)}


def git_snapshot(message: str) -> dict[str, Any]:
    settings = load_settings()
    if not bool(settings.get("git_data_snapshots_enabled", False)):
        return {
            "ok": False,
            "locked": True,
            "message": "数据 Git 快照默认关闭。当前 GitHub 仓库是公开仓库；请先将仓库改为 Private，再把 config/settings.yaml 中 git_data_snapshots_enabled 改为 true。",
        }
    status = git_status()
    if not status["available"]:
        return {"ok": False, **status}
    if not status["changes"]:
        return {"ok": True, "message": "没有需要提交的变更", "commit": ""}
    subprocess.run(["git", "add", "vault", "config"], cwd=ROOT, check=True, timeout=10)
    proc = subprocess.run(["git", "commit", "-m", message[:120] or "Update CareerVault"], cwd=ROOT, text=True, capture_output=True, timeout=15)
    if proc.returncode != 0:
        return {"ok": False, "message": proc.stderr or proc.stdout}
    sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, capture_output=True, timeout=5).stdout.strip()
    return {"ok": True, "message": proc.stdout.strip(), "commit": sha}


def dashboard() -> dict[str, Any]:
    experiences = list_experiences()
    inbox = list_inbox()
    return {
        "experience_count": len(experiences),
        "resume_ready_count": sum(1 for x in experiences if x.get("resume_ready")),
        "active_count": sum(1 for x in experiences if x.get("status") == "active"),
        "inbox_count": len(inbox),
        "recent_experiences": experiences[:5],
        "recent_inbox": inbox[:5],
        "git": git_status(),
    }
