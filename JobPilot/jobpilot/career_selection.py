from __future__ import annotations

import re
from typing import Any

CATEGORY_LABELS = {
    "education": "教育",
    "internship": "实习",
    "work": "工作",
    "project": "项目",
    "research": "科研",
    "campus": "校园",
    "award": "奖项",
    "certificate": "证书",
    "skill": "技能",
    "other": "其他",
}

STOPWORDS = {
    "岗位", "工作", "负责", "要求", "相关", "能力", "经验", "熟悉", "了解", "以及", "进行", "具有", "具备",
    "优先", "以上", "能够", "良好", "职位", "招聘", "任职", "职责", "专业", "本科", "硕士", "实习",
    "the", "and", "for", "with", "from", "this", "that", "you", "are", "job", "work", "experience",
}


def _tokens(text: str) -> set[str]:
    value = str(text or "").lower()
    english = re.findall(r"[a-z][a-z0-9+#.\-]{1,}", value)
    chinese_chunks = re.findall(r"[\u4e00-\u9fff]{2,}", value)
    chinese: list[str] = []
    for chunk in chinese_chunks:
        if len(chunk) <= 4:
            chinese.append(chunk)
        chinese.extend(chunk[i : i + 2] for i in range(max(0, len(chunk) - 1)))
    return {x for x in english + chinese if x and x not in STOPWORDS}


def _query_terms(text: str) -> list[str]:
    """Return a compact set of human-readable JD terms.

    English technical tokens and short Chinese phrases are kept; generic recruiting words are removed.
    """
    value = str(text or "")
    terms: list[str] = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9+#.\-]{1,}", value):
        cleaned = token.strip()
        if cleaned.lower() not in STOPWORDS and cleaned.lower() not in {x.lower() for x in terms}:
            terms.append(cleaned)
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,8}", value):
        if chunk in STOPWORDS:
            continue
        if chunk not in terms:
            terms.append(chunk)
    return terms[:80]


def _haystack(exp: dict[str, Any]) -> str:
    pieces = [
        exp.get("title", ""),
        exp.get("organization", ""),
        exp.get("role", ""),
        " ".join(str(x) for x in exp.get("tags", []) or []),
        " ".join(str(x) for x in exp.get("skills", []) or []),
        " ".join(str(x) for x in exp.get("domains", []) or []),
        exp.get("description", ""),
        " ".join(str(x) for x in exp.get("highlights", []) or []),
    ]
    return "\n".join(str(x or "") for x in pieces)


def explain_match(exp: dict[str, Any], query: str) -> dict[str, Any]:
    q_tokens = _tokens(query)
    e_text = _haystack(exp)
    e_tokens = _tokens(e_text)
    overlap = q_tokens & e_tokens

    query_terms = _query_terms(query)
    hay_lower = e_text.lower()
    matched_terms: list[str] = []
    for term in query_terms:
        if term.lower() in hay_lower and term.lower() not in {x.lower() for x in matched_terms}:
            matched_terms.append(term)

    skill_values = [str(x).strip() for x in (exp.get("skills") or exp.get("tags") or []) if str(x).strip()]
    matched_skills = [x for x in skill_values if x.lower() in str(query or "").lower()]
    matched_skills = list(dict.fromkeys(matched_skills))[:6]

    token_ratio = len(overlap) / max(1, min(len(q_tokens), 24)) if q_tokens else 0.0
    term_ratio = len(matched_terms) / max(1, min(len(query_terms), 14)) if query_terms else 0.0
    skill_bonus = min(0.32, 0.08 * len(matched_skills))
    score = min(1.0, token_ratio * 0.52 + term_ratio * 0.48 + skill_bonus)

    raw = exp.get("match_score")
    try:
        score = max(score, min(1.0, float(raw)))
    except (TypeError, ValueError):
        pass

    reasons: list[str] = []
    if matched_skills:
        reasons.append("技能/领域命中：" + "、".join(matched_skills))
    if matched_terms:
        reasons.append("JD 关键词命中：" + "、".join(matched_terms[:6]))
    if overlap and not matched_terms:
        reasons.append(f"经历内容与 JD 有 {len(overlap)} 个关键词重合")
    category = CATEGORY_LABELS.get(str(exp.get("category") or "other"), "经历")
    if not reasons:
        reasons.append(f"{category}事实已 Resume Ready，但与当前 JD 的直接关键词重合较少")

    return {
        "match_percent": max(0, min(100, int(round(score * 100)))),
        "match_reasons": reasons[:3],
        "matched_terms": matched_terms[:10],
        "matched_skills": matched_skills,
    }


def rank_experiences(experiences: list[dict[str, Any]], query: str, *, default_count: int = 6) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for exp in experiences:
        row = dict(exp)
        row.update(explain_match(row, query))
        ranked.append(row)
    ranked.sort(key=lambda x: (int(x.get("match_percent") or 0), str(x.get("updated_at") or "")), reverse=True)

    positive = [x for x in ranked if int(x.get("match_percent") or 0) > 0]
    selected_ids = {str(x.get("id")) for x in (positive[:default_count] if positive else ranked[: min(3, default_count)])}
    for row in ranked:
        row["selected_default"] = str(row.get("id")) in selected_ids
    return ranked


def filter_selected(experiences: list[dict[str, Any]], selected_ids: list[str]) -> list[dict[str, Any]]:
    wanted = {str(x).strip() for x in selected_ids if str(x).strip()}
    by_id = {str(x.get("id") or ""): x for x in experiences}
    return [by_id[x] for x in selected_ids if x in by_id and x in wanted]
