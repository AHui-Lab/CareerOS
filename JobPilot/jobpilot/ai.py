from __future__ import annotations

import json
import os
from typing import Any

import httpx

SYSTEM_PROMPT = """你是 JobPilot 的招聘信息结构化解析器。只输出 JSON，不要 markdown。
字段必须包括：company, role, location, deadline, description, match_score, match_reasons, risks。
match_score 为 0-100 整数。match_reasons 和 risks 是字符串数组。

解析优先级：
1. browser_context.job_posting（来自 schema.org JobPosting）优先级最高；
2. 页面正文中明确标注的“公司名称/招聘单位/岗位名称/工作地点/截止时间”；
3. browser_context.site_name、brand_candidates、headings；
4. 最后才参考 page_title。

重要规则：
- “登录、首页、官网、校园招聘、校招、招聘主页、职位列表、加入我们、提前批、个人中心”不是岗位名称。
- 如果页面只是企业招聘主页/校招专题，没有单个具体岗位，role 写“招聘主页”，不要把活动标题当成岗位。
- 如果页面是登录页，role 写“招聘登录页”。
- 公司名允许从“科大讯飞招聘”“顺丰科技2027届校园招聘”等站点品牌中去掉“招聘/校园招聘/官网/2027届…”后得到，但不能凭空猜公司。
- 不得编造网页中不存在的硬性事实；不确定字段留空字符串。
- 匹配评分要参考提供的用户偏好，但不能因为偏好信息缺失而虚构经历。
"""


def enabled() -> bool:
    return bool(os.getenv("AI_API_KEY", "").strip() and os.getenv("AI_MODEL", "").strip())


def _extract_json(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].lstrip()
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("AI 没有返回可识别的 JSON")
    return json.loads(content[start : end + 1])


async def enrich_with_ai(base: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    if not enabled():
        return base

    api_key = os.getenv("AI_API_KEY", "").strip()
    base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = os.getenv("AI_MODEL", "").strip()

    user_content = {
        "source_url": base.get("source_url", ""),
        "page_title": base.get("title", ""),
        "page_kind": base.get("page_kind", ""),
        "browser_context": base.get("_page_context") or {},
        "page_text": (base.get("raw_text") or "")[:45_000],
        "user_profile": profile,
    }

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_content, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(f"{base_url}/chat/completions", json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    ai_data = _extract_json(content)
    merged = dict(base)
    for field in ("company", "role", "location", "deadline", "description", "match_score", "match_reasons", "risks"):
        if field in ai_data and ai_data[field] not in (None, ""):
            merged[field] = ai_data[field]
    try:
        merged["match_score"] = max(0, min(100, int(merged.get("match_score", 0))))
    except Exception:
        merged["match_score"] = base.get("match_score", 0)
    if not isinstance(merged.get("match_reasons"), list):
        merged["match_reasons"] = base.get("match_reasons", [])
    if not isinstance(merged.get("risks"), list):
        merged["risks"] = base.get("risks", [])
    return merged
