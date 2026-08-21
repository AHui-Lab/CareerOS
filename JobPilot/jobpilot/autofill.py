from __future__ import annotations

import re
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _split_date_range(value: Any) -> tuple[str, str]:
    text = _text(value)
    if not text:
        return "", ""

    # A normal '-' is also part of ISO-like dates such as 2025-07, so only
    # treat it as a range separator when it has surrounding whitespace.
    spaced = re.match(r"^\s*(.+?)\s+(?:-|—|–|~|～)\s+(.+?)\s*$", text)
    if spaced:
        return spaced.group(1).strip(), spaced.group(2).strip()

    # Long dashes / wave marks are safe range separators even without spaces.
    long_sep = re.match(r"^\s*(.+?)(?:—|–|~|～)(.+?)\s*$", text)
    if long_sep:
        return long_sep.group(1).strip(), long_sep.group(2).strip()

    # Chinese textual separators are also unambiguous.
    chinese = re.match(r"^\s*(.+?)(?:至|到)(.+?)\s*$", text)
    if chinese:
        return chinese.group(1).strip(), chinese.group(2).strip()

    return text, ""


def _item_record(item: dict[str, Any]) -> dict[str, Any]:
    start, end = _split_date_range(item.get("date"))
    bullets = [str(x).strip() for x in (item.get("bullets") or []) if str(x).strip()]
    title = _text(item.get("title"))
    organization = _text(item.get("organization"))
    location = _text(item.get("location"))
    description = "\n".join(bullets)
    text = "\n".join(
        x for x in [" · ".join(y for y in [organization, title, _text(item.get("date")), location] if y), *[f"- {b}" for b in bullets]] if x
    )
    return {
        "source_id": item.get("source_id"),
        "organization": organization,
        "title": title,
        "start_date": start,
        "end_date": end,
        "date": _text(item.get("date")),
        "location": location,
        "description": description,
        "bullets": bullets,
        "text": text,
    }


def _section_kind(title: str) -> str:
    title = _text(title)
    if any(x in title for x in ("教育", "学历")):
        return "education"
    if any(x in title for x in ("实习", "工作")):
        return "internships"
    if any(x in title for x in ("项目", "作品")):
        return "projects"
    if any(x in title for x in ("科研", "研究")):
        return "research"
    if any(x in title for x in ("校园", "学生工作", "社团")):
        return "campus"
    if any(x in title for x in ("奖项", "荣誉", "获奖")):
        return "awards"
    return "other"


def flat_profile(profile: dict[str, Any]) -> dict[str, str]:
    keys = (
        "name", "phone", "email", "gender", "birth_date", "id_type", "id_number", "ethnicity", "native_place",
        "political_status", "marital_status", "household_registration", "address", "emergency_contact_name",
        "emergency_contact_phone", "current_city", "school", "college", "major", "degree", "education_start_date",
        "degree_type", "graduation_date", "gpa", "rank", "website", "portfolio_url", "github_url",
    )
    out = {key: _text(profile.get(key)) for key in keys}
    out["self_intro"] = _text(profile.get("summary"))
    return out


def build_structured_autofill(version: dict[str, Any] | None, fallback_profile: dict[str, Any]) -> dict[str, Any]:
    version = version or {}
    resume = version.get("resume") if isinstance(version.get("resume"), dict) else {}
    profile = resume.get("profile_snapshot") if isinstance(resume.get("profile_snapshot"), dict) else fallback_profile
    profile = dict(profile or {})
    # Sensitive local fields must always come from the current private profile,
    # even when the selected resume version was generated earlier.
    for key in ("id_type", "id_number", "ethnicity", "native_place", "political_status", "marital_status", "household_registration", "address", "emergency_contact_name", "emergency_contact_phone", "photo_path"):
        if _text(fallback_profile.get(key)):
            profile[key] = fallback_profile[key]

    structured: dict[str, Any] = {
        "schema_version": 2,
        "profile": flat_profile(profile),
        "education": [],
        "internships": [],
        "projects": [],
        "research": [],
        "campus": [],
        "awards": [],
        "skills": [str(x).strip() for x in (resume.get("skills") or []) if str(x).strip()],
        "resume_version": {
            "id": version.get("id"),
            "name": _text(version.get("name")),
            "target_company": _text(version.get("target_company")),
            "target_role": _text(version.get("target_role")),
        },
    }

    for section in resume.get("sections") or []:
        if not isinstance(section, dict):
            continue
        kind = _section_kind(section.get("title", ""))
        if kind == "other":
            continue
        for item in section.get("items") or []:
            if isinstance(item, dict):
                structured[kind].append(_item_record(item))

    if not structured["education"] and any(_text(profile.get(k)) for k in ("school", "major", "degree", "graduation_date")):
        structured["education"].append({
            "source_id": "profile-education",
            "organization": _text(profile.get("school")),
            "school": _text(profile.get("school")),
            "college": _text(profile.get("college")),
            "major": _text(profile.get("major")),
            "degree": _text(profile.get("degree")),
            "start_date": "",
            "end_date": _text(profile.get("graduation_date")),
            "date": _text(profile.get("graduation_date")),
            "location": "",
            "gpa": _text(profile.get("gpa")),
            "rank": _text(profile.get("rank")),
            "description": "",
            "bullets": [],
            "text": " · ".join(x for x in [_text(profile.get("school")), _text(profile.get("major")), _text(profile.get("degree")), _text(profile.get("graduation_date"))] if x),
        })
    else:
        for row in structured["education"]:
            row.setdefault("school", row.get("organization", ""))
            row.setdefault("college", _text(profile.get("college")))
            row.setdefault("major", _text(profile.get("major")))
            row.setdefault("degree", _text(profile.get("degree")))
            row.setdefault("gpa", _text(profile.get("gpa")))
            row.setdefault("rank", _text(profile.get("rank")))

    return structured


def build_flat_package(version: dict[str, Any] | None, fallback_profile: dict[str, Any]) -> dict[str, str]:
    version = version or {}
    resume = version.get("resume") if isinstance(version.get("resume"), dict) else {}
    profile = resume.get("profile_snapshot") if isinstance(resume.get("profile_snapshot"), dict) else fallback_profile
    profile = dict(profile or {})
    for key in ("id_type", "id_number", "ethnicity", "native_place", "political_status", "marital_status", "household_registration", "address", "emergency_contact_name", "emergency_contact_phone", "photo_path"):
        if _text(fallback_profile.get(key)):
            profile[key] = fallback_profile[key]
    result = flat_profile(profile)

    saved = version.get("autofill") if isinstance(version.get("autofill"), dict) else {}
    for key, value in saved.items():
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()

    structured = build_structured_autofill(version, fallback_profile)
    text_map = {
        "education_experience": "education",
        "internship_experience": "internships",
        "project_experience": "projects",
        "research_experience": "research",
        "campus_experience": "campus",
    }
    for flat_key, structured_key in text_map.items():
        if not result.get(flat_key):
            rows = structured.get(structured_key) or []
            result[flat_key] = "\n\n".join(_text(x.get("text")) for x in rows if isinstance(x, dict) and _text(x.get("text")))
    if not result.get("awards"):
        result["awards"] = "\n".join(_text(x.get("text")) for x in structured.get("awards", []) if isinstance(x, dict) and _text(x.get("text")))
    if not result.get("skills"):
        result["skills"] = "、".join(structured.get("skills") or [])
    if not result.get("self_intro"):
        result["self_intro"] = _text(resume.get("summary") or profile.get("summary"))
    return {k: _text(v) for k, v in result.items()}
