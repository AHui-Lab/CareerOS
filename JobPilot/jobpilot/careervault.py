from __future__ import annotations

import asyncio
import os
import re
from typing import Any

import httpx

DEFAULT_URL = "http://127.0.0.1:8766"


def base_url() -> str:
    return (os.getenv("CAREERVAULT_URL") or DEFAULT_URL).rstrip("/")


async def health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            response = await client.get(f"{base_url()}/api/health")
            response.raise_for_status()
            data = response.json()
            return {
                "available": bool(data.get("ok")),
                "url": base_url(),
                "version": data.get("version", ""),
                "root": data.get("root", ""),
                "error": "",
            }
    except Exception as exc:
        return {
            "available": False,
            "url": base_url(),
            "version": "",
            "root": "",
            "error": f"{type(exc).__name__}: {exc}",
        }


def _education_profile(profile: dict[str, Any]) -> dict[str, str]:
    education = profile.get("education") if isinstance(profile.get("education"), list) else []
    if not education:
        return {}
    item = education[0] if isinstance(education[0], dict) else {}
    return {
        "school": str(item.get("school") or item.get("institution") or ""),
        "college": str(item.get("college") or ""),
        "major": str(item.get("major") or ""),
        "degree": str(item.get("degree") or ""),
        "graduation_date": str(item.get("end") or item.get("graduation_date") or ""),
        "gpa": str(item.get("gpa") or ""),
        "rank": str(item.get("rank") or ""),
    }


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": str(profile.get("name") or ""),
        "phone": str(profile.get("phone") or ""),
        "email": str(profile.get("email") or ""),
        "current_city": str(profile.get("city") or profile.get("current_city") or ""),
        "website": str(profile.get("website") or ""),
        "portfolio_url": str(profile.get("portfolio") or profile.get("portfolio_url") or ""),
        "github_url": str(profile.get("github") or profile.get("github_url") or ""),
        "summary": str(profile.get("headline") or profile.get("summary") or ""),
        "skills": [str(x).strip() for x in (profile.get("skills") or []) if str(x).strip()],
        "education": profile.get("education") if isinstance(profile.get("education"), list) else [],
    }
    result.update(_education_profile(profile))
    return result


def _bullet_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in str(text or "").splitlines():
        value = re.sub(r"^\s*[-*•]+\s*", "", raw).strip()
        if value:
            lines.append(value)
    return lines


def normalize_experience(item: dict[str, Any]) -> dict[str, Any]:
    type_map = {
        "project": "project",
        "internship": "internship",
        "work": "work",
        "research": "research",
        "competition": "project",
        "award": "award",
        "certificate": "certificate",
        "education": "education",
        "campus": "campus",
        "skill": "skill",
        "other": "other",
    }
    facts = str(item.get("facts") or "")
    results = str(item.get("results") or "")
    summary = str(item.get("summary") or "")
    highlights = _bullet_lines(facts) + _bullet_lines(results)
    description = "\n".join(x for x in [summary, facts, results] if x.strip())
    tags: list[str] = []
    for value in (item.get("domains") or []) + (item.get("skills") or []):
        value = str(value).strip()
        if value and value not in tags:
            tags.append(value)
    return {
        "id": str(item.get("id") or ""),
        "category": type_map.get(str(item.get("type") or "other"), "other"),
        "title": str(item.get("title") or ""),
        "organization": str(item.get("organization") or ""),
        "role": str(item.get("role") or ""),
        "start_date": str(item.get("start") or ""),
        "end_date": str(item.get("end") or ""),
        "location": str(item.get("location") or ""),
        "description": description,
        "highlights": highlights[:12],
        "tags": tags,
        "domains": [str(x).strip() for x in (item.get("domains") or []) if str(x).strip()],
        "skills": [str(x).strip() for x in (item.get("skills") or []) if str(x).strip()],
        "source": f"careervault:{item.get('id')}",
        "match_score": item.get("match_score", 0),
        "resume_ready": bool(item.get("resume_ready", True)),
        "status": str(item.get("status") or ""),
        "updated_at": str(item.get("updated_at") or ""),
    }


async def context_for_jd(jd: str, limit: int = 10) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.post(
                f"{base_url()}/api/jobpilot/context",
                json={"jd": jd, "limit": max(1, min(limit, 20))},
            )
            response.raise_for_status()
            data = response.json()
        profile = normalize_profile(data.get("profile") if isinstance(data.get("profile"), dict) else {})
        experiences = [normalize_experience(x) for x in data.get("experiences", []) if isinstance(x, dict)]
        return {
            "profile": profile,
            "experiences": experiences,
            "version": data.get("version", ""),
            "source": "careervault",
        }
    except Exception:
        return None


async def all_resume_ready() -> dict[str, Any] | None:
    """Return the complete Resume Ready fact set for deterministic human selection.

    The recommendation UI must not depend on a top-N context response because users may
    deliberately include a lower-ranked but strategically important experience.
    """
    try:
        async with httpx.AsyncClient(timeout=3.5) as client:
            profile_req = client.get(f"{base_url()}/api/jobpilot/profile")
            exp_req = client.get(f"{base_url()}/api/jobpilot/experiences", params={"resume_ready": "true"})
            profile_res, exp_res = await asyncio.gather(profile_req, exp_req)
            profile_res.raise_for_status()
            exp_res.raise_for_status()
            raw_profile = profile_res.json()
            raw_experiences = exp_res.json()
        if not isinstance(raw_experiences, list):
            raw_experiences = []
        return {
            "profile": normalize_profile(raw_profile if isinstance(raw_profile, dict) else {}),
            "experiences": [normalize_experience(x) for x in raw_experiences if isinstance(x, dict)],
            "source": "careervault",
        }
    except Exception:
        return None
