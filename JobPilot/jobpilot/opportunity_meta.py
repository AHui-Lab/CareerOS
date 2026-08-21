from __future__ import annotations

from typing import Any

from . import db

JOB_CATEGORIES: dict[str, str] = {
    "unclassified": "未分类",
    "ai": "AI / 大模型",
    "algorithm": "算法",
    "software": "软件开发",
    "test": "测试 / 测开",
    "embedded": "嵌入式",
    "semiconductor": "半导体 / 工艺",
    "hardware": "硬件 / 电子",
    "product": "产品 / 运营",
    "other": "其他",
}


def init_opportunity_meta() -> None:
    with db.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS opportunity_meta (
                opportunity_id INTEGER PRIMARY KEY,
                job_category TEXT NOT NULL DEFAULT 'unclassified',
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_opportunity_meta_category ON opportunity_meta(job_category);
            """
        )


def get_category_map() -> dict[int, str]:
    with db.connect() as conn:
        rows = conn.execute("SELECT opportunity_id, job_category FROM opportunity_meta").fetchall()
    return {int(row["opportunity_id"]): str(row["job_category"] or "unclassified") for row in rows}


def set_category(opportunity_id: int, category: str) -> dict[str, Any] | None:
    if category not in JOB_CATEGORIES:
        raise ValueError("未知岗位类别")
    if not db.get_opportunity(opportunity_id):
        return None
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO opportunity_meta(opportunity_id, job_category, updated_at)
            VALUES (?, ?, datetime('now', 'localtime'))
            ON CONFLICT(opportunity_id) DO UPDATE SET
                job_category = excluded.job_category,
                updated_at = datetime('now', 'localtime')
            """,
            (opportunity_id, category),
        )
    return {"opportunity_id": opportunity_id, "job_category": category, "label": JOB_CATEGORIES[category]}
