from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
from collections import Counter
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
    jd_text TEXT NOT NULL DEFAULT '',
    referral_code TEXT NOT NULL DEFAULT '',
    applied_at TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS schedule_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL DEFAULT 'other',
    title TEXT NOT NULL DEFAULT '',
    event_date TEXT NOT NULL DEFAULT '',
    event_time TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    opportunity_id INTEGER,
    source TEXT NOT NULL DEFAULT 'manual',
    source_key TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_schedule_events_date ON schedule_events(event_date, event_time);

CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    gender TEXT NOT NULL DEFAULT '',
    birth_date TEXT NOT NULL DEFAULT '',
    id_type TEXT NOT NULL DEFAULT '身份证',
    id_number TEXT NOT NULL DEFAULT '',
    ethnicity TEXT NOT NULL DEFAULT '',
    native_place TEXT NOT NULL DEFAULT '',
    political_status TEXT NOT NULL DEFAULT '',
    marital_status TEXT NOT NULL DEFAULT '',
    household_registration TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    emergency_contact_name TEXT NOT NULL DEFAULT '',
    emergency_contact_phone TEXT NOT NULL DEFAULT '',
    photo_path TEXT NOT NULL DEFAULT '',
    current_city TEXT NOT NULL DEFAULT '',
    school TEXT NOT NULL DEFAULT '',
    college TEXT NOT NULL DEFAULT '',
    major TEXT NOT NULL DEFAULT '',
    degree TEXT NOT NULL DEFAULT '',
    graduation_date TEXT NOT NULL DEFAULT '',
    education_start_date TEXT NOT NULL DEFAULT '',
    degree_type TEXT NOT NULL DEFAULT '',
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

CREATE TABLE IF NOT EXISTS interview_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_type TEXT NOT NULL DEFAULT 'interview',
    source_type TEXT NOT NULL DEFAULT 'personal',
    source_key TEXT NOT NULL DEFAULT '',
    paper_name TEXT NOT NULL DEFAULT '',
    question_no INTEGER NOT NULL DEFAULT 0,
    topic TEXT NOT NULL DEFAULT '',
    role_category TEXT NOT NULL DEFAULT '',
    company TEXT NOT NULL DEFAULT '',
    opportunity_id INTEGER,
    question TEXT NOT NULL DEFAULT '',
    options TEXT NOT NULL DEFAULT '[]',
    correct_answer TEXT NOT NULL DEFAULT '',
    answer TEXT NOT NULL DEFAULT '',
    analysis TEXT NOT NULL DEFAULT '',
    feeling TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    event_date TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_interview_questions_role ON interview_questions(role_category);
CREATE INDEX IF NOT EXISTS idx_interview_questions_date ON interview_questions(event_date DESC);

CREATE TABLE IF NOT EXISTS role_field_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_category TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    self_evaluation TEXT NOT NULL DEFAULT '',
    strengths TEXT NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '[]',
    common_answers TEXT NOT NULL DEFAULT '{}',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_role_field_sets_role ON role_field_sets(role_category);

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

CREATE TABLE IF NOT EXISTS email_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    imap_host TEXT NOT NULL DEFAULT '',
    imap_port INTEGER NOT NULL DEFAULT 993,
    username TEXT NOT NULL DEFAULT '',
    password TEXT NOT NULL DEFAULT '',
    folder TEXT NOT NULL DEFAULT 'INBOX',
    last_uid INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
INSERT OR IGNORE INTO email_settings(id) VALUES (1);

CREATE TABLE IF NOT EXISTS email_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INTEGER NOT NULL,
    message_id TEXT NOT NULL DEFAULT '',
    sender TEXT NOT NULL DEFAULT '',
    subject TEXT NOT NULL DEFAULT '',
    received_at TEXT NOT NULL DEFAULT '',
    snippet TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    opportunity_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    imported_at TEXT NOT NULL DEFAULT '',
    UNIQUE(uid),
    FOREIGN KEY(opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_email_messages_received ON email_messages(received_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_messages_status ON email_messages(status);
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
        opportunity_migrations = {
            "page_kind": "ALTER TABLE opportunities ADD COLUMN page_kind TEXT NOT NULL DEFAULT 'unknown'",
            "adapter_name": "ALTER TABLE opportunities ADD COLUMN adapter_name TEXT NOT NULL DEFAULT '通用网页'",
            "page_context": "ALTER TABLE opportunities ADD COLUMN page_context TEXT NOT NULL DEFAULT '{}'",
            "note": "ALTER TABLE opportunities ADD COLUMN note TEXT NOT NULL DEFAULT ''",
            "jd_text": "ALTER TABLE opportunities ADD COLUMN jd_text TEXT NOT NULL DEFAULT ''",
            "referral_code": "ALTER TABLE opportunities ADD COLUMN referral_code TEXT NOT NULL DEFAULT ''",
            "applied_at": "ALTER TABLE opportunities ADD COLUMN applied_at TEXT NOT NULL DEFAULT ''",
        }
        schedule_columns = {row[1] for row in conn.execute("PRAGMA table_info(schedule_events)").fetchall()}
        schedule_migrations = {
            "source": "ALTER TABLE schedule_events ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'",
            "source_key": "ALTER TABLE schedule_events ADD COLUMN source_key TEXT NOT NULL DEFAULT ''",
        }
        profile_columns = {row[1] for row in conn.execute("PRAGMA table_info(profile)").fetchall()}
        profile_migrations = {
            "id_type": "ALTER TABLE profile ADD COLUMN id_type TEXT NOT NULL DEFAULT '身份证'",
            "id_number": "ALTER TABLE profile ADD COLUMN id_number TEXT NOT NULL DEFAULT ''",
            "ethnicity": "ALTER TABLE profile ADD COLUMN ethnicity TEXT NOT NULL DEFAULT ''",
            "native_place": "ALTER TABLE profile ADD COLUMN native_place TEXT NOT NULL DEFAULT ''",
            "political_status": "ALTER TABLE profile ADD COLUMN political_status TEXT NOT NULL DEFAULT ''",
            "marital_status": "ALTER TABLE profile ADD COLUMN marital_status TEXT NOT NULL DEFAULT ''",
            "household_registration": "ALTER TABLE profile ADD COLUMN household_registration TEXT NOT NULL DEFAULT ''",
            "address": "ALTER TABLE profile ADD COLUMN address TEXT NOT NULL DEFAULT ''",
            "emergency_contact_name": "ALTER TABLE profile ADD COLUMN emergency_contact_name TEXT NOT NULL DEFAULT ''",
            "emergency_contact_phone": "ALTER TABLE profile ADD COLUMN emergency_contact_phone TEXT NOT NULL DEFAULT ''",
            "photo_path": "ALTER TABLE profile ADD COLUMN photo_path TEXT NOT NULL DEFAULT ''",
            "education_start_date": "ALTER TABLE profile ADD COLUMN education_start_date TEXT NOT NULL DEFAULT ''",
            "degree_type": "ALTER TABLE profile ADD COLUMN degree_type TEXT NOT NULL DEFAULT ''",
        }
        question_columns = {row[1] for row in conn.execute("PRAGMA table_info(interview_questions)").fetchall()}
        question_migrations = {
            "source_key": "ALTER TABLE interview_questions ADD COLUMN source_key TEXT NOT NULL DEFAULT ''",
            "paper_name": "ALTER TABLE interview_questions ADD COLUMN paper_name TEXT NOT NULL DEFAULT ''",
            "question_no": "ALTER TABLE interview_questions ADD COLUMN question_no INTEGER NOT NULL DEFAULT 0",
            "topic": "ALTER TABLE interview_questions ADD COLUMN topic TEXT NOT NULL DEFAULT ''",
            "options": "ALTER TABLE interview_questions ADD COLUMN options TEXT NOT NULL DEFAULT '[]'",
            "correct_answer": "ALTER TABLE interview_questions ADD COLUMN correct_answer TEXT NOT NULL DEFAULT ''",
            "analysis": "ALTER TABLE interview_questions ADD COLUMN analysis TEXT NOT NULL DEFAULT ''",
        }
        for column, sql in opportunity_migrations.items():
            if column not in columns:
                conn.execute(sql)
        for column, sql in schedule_migrations.items():
            if column not in schedule_columns:
                conn.execute(sql)
        for column, sql in profile_migrations.items():
            if column not in profile_columns:
                conn.execute(sql)
        for column, sql in question_migrations.items():
            if column not in question_columns:
                conn.execute(sql)
        seed_interview_question_bank(conn)
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


QUESTION_BANK_DIR = ROOT / "data" / "question-bank"
SHUNFENG_TOPICS = {
    1: "用户增长", 2: "物流业务", 3: "交互设计", 4: "交互设计", 5: "数据分析",
    6: "技术基础", 7: "用户研究", 8: "项目管理", 9: "AI 产品", 10: "数据分析",
    11: "产品策略", 12: "商业模式", 13: "AI 产品", 14: "商业分析", 15: "AI 产品",
    16: "物流业务", 17: "数据分析", 18: "产品策略", 19: "用户增长", 20: "项目管理",
    21: "AI 产品", 22: "AI 产品", 23: "数据分析", 24: "AI 产品",
}
SHUNFENG_ANALYSIS = {
    1: "Hooked Model 的闭环是触发、行动、多变的酬赏、投入；投入会提高用户再次进入闭环的可能性。",
    2: "DDP 要求卖方承担运至指定目的地的费用和风险，并负责进口清关、关税等义务。",
    3: "菲茨定律中目标越小、距离越远越难点击；屏幕右上角的小图标同时受到距离和尺寸的不利影响。",
    4: "拇指热区、内容优先和分步降低认知负担，都是移动端常见的体验设计原则。首页堆满功能会增加选择成本。",
    5: "均值改善伴随波动显著扩大，说明不同用户或场景的体验可能分化；应先查稳定性和风险，再决定是否全量。",
    6: "REST 强调用 HTTP 方法表达操作、无状态和状态码表达结果；URL 通常表达资源，而不是动作。",
    7: "问卷应从易到难、保持中立，并尽量让选项互斥且穷尽；题目越多不代表信息质量越高。",
    8: "识别风险后需要透明沟通、更新 Backlog 和评估范围；是否砍需求应由团队、PO 和 SM 基于影响共同决定。",
    9: "RAG 先检索可信知识，再把相关上下文交给模型，可约束回答范围并降低凭空编造的概率。",
    10: "UV 是独立用户数，PV 允许同一用户重复点击；3500 PV 不等于 3500 个用户，重复点击可能提示操作困惑。",
    11: "规则引擎先覆盖高频、边界相对清晰的 SKU，是在期限内保留智能价值并降低实现复杂度的 MVP。",
    12: "订阅制评估必须看成本、客户使用频次与客单价分布，以及司机侧接受度和迁移阻力。",
    13: "迁移学习可以利用其他城市的通用规律，再用少量本地数据校准，适合目标城市样本不足的情况。",
    14: "行业集中度低且竞争者实力接近时，竞争者之间更容易陷入直接比拼，竞争强度通常更高。",
    15: "生成式 AI 更适合开放式语言任务，如生成回复、抽取条款和多语言表达；路径优化应优先使用专门算法。",
    16: "最后一公里的距离未必最长，但配送地址分散、约束复杂且直接影响用户体验，因此成本和服务压力集中。",
    17: "留存要结合行业和同期群看；曲线变平说明留下来的用户形成了稳定价值，但不代表新增用户质量一定相同。",
    18: "不能只看转化提升，还要看增量成本、长期价值和可持续性；免运费通常更容易控制补贴外溢和财务风险。",
    19: "K=0.8 表示平均每个用户带来的新增用户不足 1 个，无法仅靠传播实现持续自增长。",
    20: "甘特图按时间轴展示任务，PERT 用网络关系展示任务依赖和关键路径，两者的核心表达方式不同。",
    21: "模型推荐之外还要加属性约束、规则校验和人工兜底，避免模型输出直接突破冷链等硬性业务规则。",
    22: "对比模式把推荐依据和预期收益可视化，能降低黑盒感，让业务方基于证据理解 AI 建议。",
    23: "A/B 测试通过对照组隔离同期变化，是估计 AI 功能净影响的优先方案；单纯比较前后数据会混入 KPI 变更影响。",
    24: "监控既要看输出误差和置信度，也要看输入特征漂移；训练集 Loss 下降不能代表线上效果没有衰退。",
}


def _parse_question_bank_file(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
    is_shunfeng = "shunfeng" in path.stem.lower()
    company = "顺丰" if is_shunfeng else "OPPO"
    role_category = "产品经理" if is_shunfeng else "应用后端开发"
    items: list[dict[str, Any]] = []
    question_starts = list(re.finditer(r"^#{2,3}\s*第(\d+)题(?:（([^）]+)）)?\s*$", text, flags=re.MULTILINE))
    for index, start in enumerate(question_starts):
        block = text[start.start():question_starts[index + 1].start() if index + 1 < len(question_starts) else len(text)]
        number = int(start.group(1))
        type_name = start.group(2) or ""
        prefix = text[:start.start()]
        section_types = re.findall(r"^##\s*(单选题|多选题|编程题)\s*$", prefix, flags=re.MULTILINE)
        type_name = type_name or (section_types[-1] if section_types else "")
        question_match = re.search(r"\*\*题目：\*\*\s*(.+?)(?=\n\n\*\*选项：\*\*)", block, flags=re.DOTALL)
        answer_match = re.search(r"\*\*答案：\s*([^*\n]+)\*\*", block)
        if question_match:
            question = question_match.group(1).strip()
        else:
            lines = block.splitlines()[1:]
            question_lines = []
            for line in lines:
                if re.match(r"^- [A-D]\.\s*", line) or line.strip() == "---":
                    break
                if line.strip() and not line.startswith("##"):
                    question_lines.append(line.strip())
            question = "\n".join(question_lines).strip()
        if not question:
            continue
        options = [{"key": key, "text": value.strip()} for key, value in re.findall(r"^- ([A-D])\.\s*(.+)$", block, flags=re.MULTILINE)]
        correct = answer_match.group(1).strip() if answer_match else ""
        topic = SHUNFENG_TOPICS.get(number, "综合产品能力") if is_shunfeng else "计算机基础"
        items.append({
            "source_key": f"{path.stem}:{number}",
            "paper_name": title,
            "question_no": number,
            "topic": topic,
            "question_type": "written_test",
            "source_type": "network",
            "role_category": role_category,
            "company": company,
            "question": question,
            "options": options,
            "correct_answer": correct,
            "answer": f"正确选项：{correct}" if correct else "",
            "analysis": SHUNFENG_ANALYSIS.get(number, "建议结合产品目标、用户价值和业务约束分析。") if is_shunfeng else "",
            "tags": [topic, "顺丰2027校招" if is_shunfeng else "OPPO2027秋招"],
            "event_date": "",
        })
    programming_match = re.search(r"^#{2,3}\s*编程题\s*$", text, flags=re.MULTILINE)
    if programming_match:
        programming_text = text[programming_match.end():]
        programming_items = list(re.finditer(r"^#{2,3}\s*题目(\d+)：\s*(.+)$", programming_text, flags=re.MULTILINE))
        offset = max((item["question_no"] for item in items), default=0)
        for index, start in enumerate(programming_items):
            end = programming_items[index + 1].start() if index + 1 < len(programming_items) else len(programming_text)
            question = re.sub(r"^#{2,3}\s*", "", programming_text[start.start():end].strip().strip("-").strip(), count=1)
            programming_no = offset + int(start.group(1))
            items.append({
                "source_key": f"{path.stem}:programming-{start.group(1)}",
                "paper_name": title,
                "question_no": programming_no,
                "topic": "编程题",
                "question_type": "written_test",
                "source_type": "network",
                "role_category": role_category,
                "company": company,
                "question": question,
                "options": [],
                "correct_answer": "",
                "answer": "",
                "analysis": "",
                "tags": ["编程题", "顺丰2027校招" if is_shunfeng else "OPPO2027秋招"],
                "event_date": "",
            })
    return items


def seed_interview_question_bank(conn: sqlite3.Connection) -> None:
    if not QUESTION_BANK_DIR.exists():
        return
    for path in sorted(QUESTION_BANK_DIR.glob("*.md")):
        for item in _parse_question_bank_file(path):
            exists = conn.execute("SELECT 1 FROM interview_questions WHERE source_key = ? LIMIT 1", (item["source_key"],)).fetchone()
            if exists:
                continue
            fields = ["source_key", "paper_name", "question_no", "topic", "question_type", "source_type", "role_category", "company", "question", "options", "correct_answer", "answer", "analysis", "tags", "event_date"]
            values = [item[field] for field in fields]
            values[9] = json.dumps(values[9], ensure_ascii=False)
            values[13] = json.dumps(values[13], ensure_ascii=False)
            conn.execute(f"INSERT INTO interview_questions ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", values)


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


def get_email_settings() -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT id, imap_host, imap_port, username, folder, last_uid, updated_at FROM email_settings WHERE id = 1").fetchone()
    return dict(row) if row else {"id": 1, "imap_port": 993, "folder": "INBOX", "last_uid": 0}


def save_email_settings(fields: dict[str, Any]) -> dict[str, Any]:
    allowed = {"imap_host", "imap_port", "username", "password", "folder", "last_uid"}
    clean = {key: fields[key] for key in fields if key in allowed}
    if "imap_port" in clean:
        clean["imap_port"] = int(clean["imap_port"] or 993)
    if clean:
        with connect() as conn:
            conn.execute(
                f"UPDATE email_settings SET {', '.join(f'{field} = ?' for field in clean)}, updated_at = datetime('now', 'localtime') WHERE id = 1",
                [*clean.values()],
            )
    return get_email_settings()


def get_email_password() -> str:
    with connect() as conn:
        row = conn.execute("SELECT password FROM email_settings WHERE id = 1").fetchone()
    return str(row[0] or "") if row else ""


def insert_email_messages(items: list[dict[str, Any]]) -> int:
    if not items:
        return 0
    with connect() as conn:
        before = conn.total_changes
        for item in items:
            conn.execute(
                "INSERT OR IGNORE INTO email_messages(uid, message_id, sender, subject, received_at, snippet, body) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [item.get(key, "") for key in ("uid", "message_id", "sender", "subject", "received_at", "snippet", "body")],
            )
        return conn.total_changes - before


def list_email_messages(*, include_ignored: bool = False) -> list[dict[str, Any]]:
    query = "SELECT e.*, o.company, o.role FROM email_messages e LEFT JOIN opportunities o ON o.id = e.opportunity_id"
    if not include_ignored:
        query += " WHERE e.status != 'ignored'"
    query += " ORDER BY e.received_at DESC, e.id DESC"
    with connect() as conn:
        rows = conn.execute(query).fetchall()
    return [dict(row) for row in rows]


def update_email_message(email_id: int, *, status: str | None = None, opportunity_id: int | None = None, clear_opportunity: bool = False) -> dict[str, Any] | None:
    fields: dict[str, Any] = {}
    if status is not None: fields["status"] = status
    if opportunity_id is not None: fields["opportunity_id"] = opportunity_id
    elif clear_opportunity: fields["opportunity_id"] = None
    if status == "imported": fields["imported_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if fields:
        with connect() as conn:
            conn.execute(f"UPDATE email_messages SET {', '.join(f'{key} = ?' for key in fields)} WHERE id = ?", [*fields.values(), email_id])
    with connect() as conn:
        row = conn.execute("SELECT * FROM email_messages WHERE id = ?", (email_id,)).fetchone()
    return dict(row) if row else None


def ignore_pending_email_messages() -> int:
    with connect() as conn:
        cursor = conn.execute("UPDATE email_messages SET status = 'ignored' WHERE status = 'pending'")
    return cursor.rowcount


def advance_email_uid(uid: int) -> None:
    with connect() as conn:
        conn.execute("UPDATE email_settings SET last_uid = MAX(last_uid, ?), updated_at = datetime('now', 'localtime') WHERE id = 1", (uid,))


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
        "description", "raw_text", "jd_text", "referral_code", "applied_at", "note", "match_score", "match_reasons", "risks", "status",
        "page_kind", "adapter_name", "page_context"
    )
    payload = _serialized_opportunity(item)
    if not payload.get("jd_text"):
        payload["jd_text"] = payload.get("description", "") or payload.get("raw_text", "")
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
    allowed = {"company", "role", "location", "deadline", "applied_at", "note", "jd_text", "referral_code"}
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
        current = conn.execute("SELECT applied_at FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
        applied_at = current[0] if current else ""
        if status == "applied" and not applied_at:
            applied_at = datetime.now().strftime("%Y-%m-%d")
        conn.execute("UPDATE opportunities SET status = ?, applied_at = ?, updated_at = datetime('now', 'localtime') WHERE id = ?", (status, applied_at, opportunity_id))
    return get_opportunity(opportunity_id)


def delete_opportunity(opportunity_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM opportunities WHERE id = ?", (opportunity_id,))
    return cursor.rowcount > 0


# --- schedule / calendar ---
SCHEDULE_EVENT_FIELDS = {"event_type", "title", "event_date", "event_time", "location", "notes", "opportunity_id"}


def _schedule_event_row(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_schedule_events(*, start: str = "", end: str = "") -> list[dict[str, Any]]:
    query = "SELECT e.*, o.company, o.role FROM schedule_events e LEFT JOIN opportunities o ON o.id = e.opportunity_id"
    params: list[Any] = []
    filters = []
    if start:
        filters.append("e.event_date >= ?"); params.append(start)
    if end:
        filters.append("e.event_date <= ?"); params.append(end)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY e.event_date ASC, e.event_time ASC, e.id ASC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_schedule_event_row(row) for row in rows]


def _calendar_date(value: Any) -> str:
    text = str(value or "").strip()
    chinese = re.search(r"(\d{4})[年./-](\d{1,2})[月./-](\d{1,2})日?", text)
    if chinese:
        text = f"{chinese.group(1)}-{int(chinese.group(2)):02d}-{int(chinese.group(3)):02d}"
    else:
        text = text[:10]
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def sync_opportunity_calendar() -> None:
    """Keep automatic application/deadline events in sync with opportunity fields."""
    with connect() as conn:
        opportunities = conn.execute("SELECT id, company, role, title, status, applied_at, deadline FROM opportunities").fetchall()
        desired: dict[str, dict[str, Any]] = {}
        for row in opportunities:
            oid = int(row["id"]); label = str(row["company"] or row["role"] or row["title"] or "岗位").strip()
            applied = _calendar_date(row["applied_at"])
            if applied:
                desired[f"application:{oid}"] = {"event_type": "application", "title": f"已投递 · {label}", "event_date": applied, "event_time": "", "location": "", "notes": "由岗位投递时间自动生成，可在岗位详情中修改。", "opportunity_id": oid}
            deadline = _calendar_date(row["deadline"])
            if deadline:
                desired[f"deadline:{oid}"] = {"event_type": "deadline", "title": f"截止 · {label}", "event_date": deadline, "event_time": "", "location": "", "notes": "由岗位截止时间自动生成，可在岗位详情中修改。", "opportunity_id": oid}
        existing = {str(row["source_key"]): row for row in conn.execute("SELECT * FROM schedule_events WHERE source = 'opportunity'").fetchall()}
        for key, item in desired.items():
            if key in existing:
                conn.execute("UPDATE schedule_events SET event_type=?, title=?, event_date=?, event_time=?, location=?, notes=?, opportunity_id=?, updated_at=datetime('now','localtime') WHERE id=?", (*[item[x] for x in ("event_type", "title", "event_date", "event_time", "location", "notes", "opportunity_id")], existing[key]["id"]))
            else:
                conn.execute("INSERT INTO schedule_events(event_type,title,event_date,event_time,location,notes,opportunity_id,source,source_key) VALUES(?,?,?,?,?,?,?,?,?)", (*[item[x] for x in ("event_type", "title", "event_date", "event_time", "location", "notes", "opportunity_id")], "opportunity", key))
        for key, row in existing.items():
            if key not in desired:
                conn.execute("DELETE FROM schedule_events WHERE id=?", (row["id"],))


def get_schedule_event(event_id: int) -> dict[str, Any] | None:
    rows = list_schedule_events()
    return next((row for row in rows if int(row["id"]) == event_id), None)


def insert_schedule_event(item: dict[str, Any]) -> dict[str, Any]:
    fields = ["event_type", "title", "event_date", "event_time", "location", "notes", "opportunity_id", "source", "source_key"]
    payload = {field: item.get(field, "") for field in fields}
    payload["opportunity_id"] = int(payload["opportunity_id"]) if payload["opportunity_id"] else None
    payload["source"] = "manual"
    payload["source_key"] = ""
    with connect() as conn:
        cursor = conn.execute(
            f"INSERT INTO schedule_events ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
            [payload[field] for field in fields],
        )
        event_id = int(cursor.lastrowid)
    return get_schedule_event(event_id) or {}


def update_schedule_event(event_id: int, fields: dict[str, Any]) -> dict[str, Any] | None:
    if not get_schedule_event(event_id):
        return None
    clean = {key: fields[key] for key in fields if key in SCHEDULE_EVENT_FIELDS}
    if "opportunity_id" in clean:
        clean["opportunity_id"] = int(clean["opportunity_id"]) if clean["opportunity_id"] else None
    if clean:
        with connect() as conn:
            conn.execute(
                f"UPDATE schedule_events SET {', '.join(f'{field} = ?' for field in clean)}, updated_at = datetime('now', 'localtime') WHERE id = ?",
                [*clean.values(), event_id],
            )
    return get_schedule_event(event_id)


def delete_schedule_event(event_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM schedule_events WHERE id = ?", (event_id,))
    return cursor.rowcount > 0


# --- profile ---
PROFILE_FIELDS = {
    "name", "phone", "email", "gender", "birth_date", "id_type", "id_number", "ethnicity", "native_place",
    "political_status", "marital_status", "household_registration", "address", "emergency_contact_name",
    "emergency_contact_phone", "photo_path", "current_city", "school", "college", "major", "degree",
    "graduation_date", "education_start_date", "degree_type", "gpa", "rank", "website", "portfolio_url", "github_url", "summary"
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


def delete_resume_version(version_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM resume_versions WHERE id = ?", (version_id,))
    return cursor.rowcount > 0


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


# --- interview / written-test question bank ---
INTERVIEW_QUESTION_FIELDS = {"question_type", "source_type", "source_key", "paper_name", "question_no", "topic", "role_category", "company", "opportunity_id", "question", "options", "correct_answer", "answer", "analysis", "feeling", "tags", "event_date"}


def _question_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["tags"] = _loads(result.get("tags"), [])
    result["options"] = _loads(result.get("options"), [])
    return result


def list_interview_questions(*, role_category: str = "", source_type: str = "", question_type: str = "", topic: str = "", paper_name: str = "", search: str = "") -> list[dict[str, Any]]:
    where, params = [], []
    if role_category:
        where.append("role_category = ?"); params.append(role_category)
    if source_type:
        where.append("source_type = ?"); params.append(source_type)
    if question_type:
        where.append("question_type = ?"); params.append(question_type)
    if topic:
        where.append("topic = ?"); params.append(topic)
    if paper_name:
        where.append("paper_name = ?"); params.append(paper_name)
    if search:
        needle = f"%{search}%"
        where.append("(question LIKE ? OR answer LIKE ? OR analysis LIKE ? OR paper_name LIKE ? OR topic LIKE ? OR tags LIKE ?)")
        params.extend([needle] * 6)
    sql = "SELECT * FROM interview_questions" + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY CASE WHEN question_no > 0 THEN question_no ELSE 999999 END, event_date DESC, updated_at DESC, id DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_question_row(row) for row in rows]


def get_interview_question(question_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM interview_questions WHERE id = ?", (question_id,)).fetchone()
    return _question_row(row) if row else None


def save_interview_question(item: dict[str, Any], question_id: int | None = None) -> dict[str, Any]:
    clean = {key: item.get(key) for key in INTERVIEW_QUESTION_FIELDS if key in item}
    if "tags" in clean:
        clean["tags"] = json.dumps(clean.get("tags") or [], ensure_ascii=False)
    if "options" in clean:
        clean["options"] = json.dumps(clean.get("options") or [], ensure_ascii=False)
    clean["opportunity_id"] = int(clean["opportunity_id"]) if clean.get("opportunity_id") else None
    if question_id:
        sets = ", ".join(f"{key} = ?" for key in clean)
        with connect() as conn:
            conn.execute(f"UPDATE interview_questions SET {sets}, updated_at = datetime('now', 'localtime') WHERE id = ?", [*clean.values(), question_id])
        return get_interview_question(question_id) or {}
    fields = list(clean)
    with connect() as conn:
        cur = conn.execute(f"INSERT INTO interview_questions ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", [clean[field] for field in fields])
        new_id = int(cur.lastrowid)
    return get_interview_question(new_id) or {}


def delete_interview_question(question_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM interview_questions WHERE id = ?", (question_id,))
    return cursor.rowcount > 0


def analyze_interview_questions() -> dict[str, Any]:
    items = list_interview_questions()
    topics = Counter(item.get("topic") or "未分类" for item in items)
    papers = Counter(item.get("paper_name") or "未命名试卷" for item in items)
    types = Counter(item.get("question_type") or "interview" for item in items)
    answered = sum(1 for item in items if item.get("answer") or item.get("analysis") or item.get("correct_answer"))
    return {
        "total": len(items),
        "written_test": types.get("written_test", 0),
        "interview": types.get("interview", 0),
        "answered": answered,
        "topics": [{"name": name, "count": count} for name, count in topics.most_common()],
        "papers": [{"name": name, "count": count} for name, count in papers.most_common()],
    }


# --- reusable role-specific application fields ---
ROLE_FIELD_SET_FIELDS = {"role_category", "title", "self_evaluation", "strengths", "skills", "common_answers", "notes"}


def _role_field_row(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["skills"] = _loads(result.get("skills"), [])
    result["common_answers"] = _loads(result.get("common_answers"), {})
    return result


def list_role_field_sets(role_category: str = "") -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM role_field_sets" + (" WHERE role_category = ?" if role_category else "") + " ORDER BY updated_at DESC, id DESC", (role_category,) if role_category else ()).fetchall()
    return [_role_field_row(row) for row in rows]


def get_role_field_set(field_set_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM role_field_sets WHERE id = ?", (field_set_id,)).fetchone()
    return _role_field_row(row) if row else None


def save_role_field_set(item: dict[str, Any], field_set_id: int | None = None) -> dict[str, Any]:
    clean = {key: item.get(key) for key in ROLE_FIELD_SET_FIELDS if key in item}
    clean["skills"] = json.dumps(clean.get("skills") or [], ensure_ascii=False)
    clean["common_answers"] = json.dumps(clean.get("common_answers") or {}, ensure_ascii=False)
    if field_set_id:
        sets = ", ".join(f"{key} = ?" for key in clean)
        with connect() as conn:
            conn.execute(f"UPDATE role_field_sets SET {sets}, updated_at = datetime('now', 'localtime') WHERE id = ?", [*clean.values(), field_set_id])
        return get_role_field_set(field_set_id) or {}
    fields = list(clean)
    with connect() as conn:
        cur = conn.execute(f"INSERT INTO role_field_sets ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})", [clean[field] for field in fields])
        new_id = int(cur.lastrowid)
    return get_role_field_set(new_id) or {}


def delete_role_field_set(field_set_id: int) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM role_field_sets WHERE id = ?", (field_set_id,))
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
