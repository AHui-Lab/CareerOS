from __future__ import annotations

from .store import EXPERIENCES, atomic_write, dump_frontmatter, get_experience, now_iso, split_frontmatter


def complete_migration_review(experience_id: str, *, resume_ready: bool = False) -> dict:
    """Mark one legacy-migrated experience as explicitly reviewed.

    The operation is intentionally separate from the normal experience PATCH route so
    ordinary autosave can never silently clear the migration safety gate.
    """
    path = EXPERIENCES / experience_id / "index.md"
    if not path.exists():
        raise FileNotFoundError(experience_id)

    text = path.read_text(encoding="utf-8")
    meta, body = split_frontmatter(text)

    if meta.get("migration_review") != "required":
        return get_experience(experience_id)

    meta["migration_review"] = "completed"
    meta["migration_reviewed_at"] = now_iso()
    meta["resume_ready"] = bool(resume_ready)
    if meta.get("status") == "draft":
        meta["status"] = "verified"
    meta["updated_at"] = now_iso()

    atomic_write(path, dump_frontmatter(meta, body))
    return get_experience(experience_id)
