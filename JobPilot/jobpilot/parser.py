from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

from .security import validate_public_http_url
from .adapters import apply_site_adapter

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "profile.json"
PROFILE_EXAMPLE_PATH = ROOT / "data" / "profile.example.json"

DATE_PATTERNS = [
    r"(?:网申|报名|申请|投递)?截止(?:时间|日期)?[：:\s]*([0-9]{4}[年./-][0-9]{1,2}[月./-][0-9]{1,2}日?)",
    r"(?:网申|报名|申请|投递)?截止(?:时间|日期)?[：:\s]*([0-9]{1,2}[月./-][0-9]{1,2}日?)",
    r"(?:valid\s*through|deadline)[：:\s]*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
]

FIELD_PATTERNS = {
    "company": [
        r"(?:公司名称|招聘单位|单位名称|企业名称|雇主名称)[：:\s]+([^\n]{2,80})",
    ],
    "role": [
        r"(?:职位名称|岗位名称|招聘岗位|应聘岗位|应聘职位|职位)[：:\s]+([^\n]{2,100})",
    ],
    "location": [
        r"(?:工作地点|工作城市|办公地点|工作地址|地点)[：:\s]+([^\n]{2,100})",
    ],
}

ROLE_HINTS = re.compile(
    r"工程师|经理|专员|设计师|设计|运营|策划|研发|开发|测试|产品|销售|算法|数据|财务|法务|"
    r"人力|HR|实习|管培|顾问|研究员|研究|采购|供应链|音频|音乐|内容|市场|品牌|行政|"
    r"项目经理|项目管理|分析师|分析|客服|视觉|交互|前端|后端|客户端|服务端|架构|安全|审计|商务|编辑|编导|"
    r"教师|助理|岗位|职位",
    re.IGNORECASE,
)

NOISE_EXACT = {
    "登录", "登陆", "login", "sign in", "signin", "首页", "home", "官网", "招聘", "招聘官网",
    "校园招聘", "校招", "社会招聘", "社招", "职位", "职位列表", "招聘职位", "人才招聘", "加入我们",
    "career", "careers", "招聘门户", "人才门户", "招聘平台", "个人中心", "我的申请", "注册",
    "职位详情", "岗位详情", "职位搜索", "岗位搜索", "招聘项目", "校园招聘项目",
}

NOISE_ROLE_PHRASES = (
    "招聘官网", "校园招聘官网", "招聘主页", "招聘首页", "职位列表", "全部职位", "搜索职位", "人才招聘",
    "人才官网", "加入我们", "登录", "注册", "官网", "提前批", "校园招聘", "校招", "社会招聘",
    "职位详情", "岗位详情", "招聘项目", "校园招聘项目",
)

COMPANY_SUFFIXES = [
    "校园招聘官网", "校园招聘", "校招官网", "校招", "社会招聘", "社招", "人才招聘官网", "人才招聘",
    "招聘官网", "招聘平台", "招聘门户", "人才门户", "招聘", "官方招聘", "官网", "官方网站", "人才",
    "careers", "career", "jobs", "job",
]


def normalize_text(text: str) -> str:
    text = (text or "").replace("\u00a0", " ").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _safe_json(value: str) -> Any:
    try:
        return json.loads(value)
    except Exception:
        return None


def _walk_jsonld(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_jsonld(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_jsonld(child)


def _jsonld_job_posting_from_soup(soup: BeautifulSoup) -> dict[str, Any]:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        data = _safe_json(script.string or script.get_text("", strip=True))
        if data is None:
            continue
        for obj in _walk_jsonld(data):
            obj_type = obj.get("@type")
            types = obj_type if isinstance(obj_type, list) else [obj_type]
            if any(str(t).lower() == "jobposting" for t in types if t):
                return obj
    return {}


def _location_from_jobposting(job: dict[str, Any]) -> str:
    locations = job.get("jobLocation") or job.get("applicantLocationRequirements") or []
    if not isinstance(locations, list):
        locations = [locations]
    pieces: list[str] = []
    for loc in locations:
        if not isinstance(loc, dict):
            continue
        address = loc.get("address", loc)
        if isinstance(address, str):
            pieces.append(address)
            continue
        if isinstance(address, dict):
            for key in ("addressLocality", "addressRegion", "streetAddress", "addressCountry"):
                value = address.get(key)
                if isinstance(value, dict):
                    value = value.get("name")
                if value and str(value) not in pieces:
                    pieces.append(str(value))
    return " ".join(pieces[:4]).strip()


def _company_from_jobposting(job: dict[str, Any]) -> str:
    org = job.get("hiringOrganization") or job.get("organization") or {}
    if isinstance(org, str):
        return normalize_text(org)
    if isinstance(org, dict):
        return normalize_text(str(org.get("name") or ""))
    return ""


def _context_from_jobposting(job: dict[str, Any]) -> dict[str, Any]:
    if not job:
        return {}
    return {
        "title": normalize_text(str(job.get("title") or "")),
        "company": _company_from_jobposting(job),
        "location": _location_from_jobposting(job),
        "deadline": normalize_text(str(job.get("validThrough") or "")),
        "date_posted": normalize_text(str(job.get("datePosted") or "")),
        "employment_type": job.get("employmentType") or "",
    }


def extract_page(html: str) -> tuple[str, str, dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    jobposting = _jsonld_job_posting_from_soup(soup)

    def meta_content(*, name: str = "", prop: str = "") -> str:
        attrs = {"name": name} if name else {"property": prop}
        tag = soup.find("meta", attrs=attrs)
        return normalize_text(tag.get("content", "")) if tag and tag.get("content") else ""

    title = meta_content(prop="og:title")
    if not title and soup.title:
        title = normalize_text(soup.title.get_text(" ", strip=True))

    site_name = meta_content(prop="og:site_name") or meta_content(name="application-name")
    description = meta_content(name="description") or meta_content(prop="og:description")
    headings = [normalize_text(h.get_text(" ", strip=True)) for h in soup.find_all(["h1", "h2"])[:20]]
    headings = [x for x in headings if x]

    brand_candidates: list[str] = []
    for selector in ["header img", "[class*='logo'] img", "img[class*='logo']", "header [class*='brand']"]:
        for el in soup.select(selector)[:10]:
            for attr in ("alt", "title"):
                value = normalize_text(str(el.get(attr) or ""))
                if value and value not in brand_candidates:
                    brand_candidates.append(value)
            if getattr(el, "get_text", None):
                value = normalize_text(el.get_text(" ", strip=True))
                if value and len(value) <= 80 and value not in brand_candidates:
                    brand_candidates.append(value)

    main_text = ""
    for selector in ["main", "[role='main']", ".job-detail", ".jobDetail", ".position-detail", ".positionDetail"]:
        candidates = soup.select(selector)
        if candidates:
            candidate = max((normalize_text(el.get_text("\n", strip=True)) for el in candidates), key=len, default="")
            if len(candidate) > len(main_text):
                main_text = candidate

    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    text = normalize_text(soup.get_text("\n", strip=True))
    context = {
        "site_name": site_name,
        "description": description,
        "headings": headings,
        "brand_candidates": brand_candidates[:20],
        "main_text": main_text[:120_000],
        "job_posting": _context_from_jobposting(jobposting),
    }
    return title, text, context


def extract_visible_text(html: str) -> tuple[str, str]:
    title, text, _ = extract_page(html)
    return title, text


def _first_match(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return normalize_text(match.group(1))[:160]
    return ""


def _brand_from_title(title: str) -> str:
    """Extract a likely employer brand from campaign/career page titles."""
    value = normalize_text(title)
    if not value:
        return ""
    first = re.split(r"[-_|｜—–·]", value, maxsplit=1)[0].strip()
    candidates = [first, value]
    patterns = [
        r"^(.{2,60}?)(?:人才)?(?:20)?\d{2}届",
        r"^(.{2,60}?)(?:校园招聘|校招|人才招聘|招聘官网|招聘平台|招聘门户|官方招聘|招聘)",
    ]
    for candidate in candidates:
        for pattern in patterns:
            m = re.search(pattern, candidate, flags=re.IGNORECASE)
            if m:
                cleaned = _clean_company_candidate(m.group(1))
                if cleaned:
                    return cleaned
    return ""


def _is_placeholder(value: str) -> bool:
    return normalize_text(value) in {"", "待识别公司", "待识别岗位", "未知公司", "未知岗位", "招聘公司", "招聘岗位"}


def _clean_company_candidate(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r"^[\-_|｜—–·\s]+|[\-_|｜—–·\s]+$", "", value)
    value = re.sub(r"(?:人才)?(?:20)?\d{2}届.*$", "", value)
    value = re.sub(r"(?:20)?\d{2}[届级].*$", "", value)
    for suffix in sorted(COMPANY_SUFFIXES, key=len, reverse=True):
        value = re.sub(rf"\s*{re.escape(suffix)}\s*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"(?:202\d|20\d{2})\s*(?:校园)?招聘.*$", "", value)
    value = normalize_text(value).strip("-_|｜—–· ")
    if not value or value.lower() in NOISE_EXACT:
        return ""
    if len(value) < 2 or len(value) > 80:
        return ""
    if ROLE_HINTS.search(value) and not re.search(r"公司|集团|科技|银行|航空|研究院|事务所|医院|大学|学院|证券|汽车|电子|通信|股份|有限", value):
        return ""
    return value


def _looks_like_role(value: str) -> bool:
    value = normalize_text(value)
    lower = value.lower()
    if not value or lower in NOISE_EXACT or len(value) < 2 or len(value) > 100:
        return False
    if any(phrase.lower() == lower for phrase in NOISE_ROLE_PHRASES):
        return False
    if re.search(r"(?:20)?\d{2}届.*(?:招聘|提前批|校招)", value):
        return False
    return bool(ROLE_HINTS.search(value))


def _clean_role_candidate(value: str) -> str:
    value = normalize_text(value).strip("-_|｜—–· ")
    if _looks_like_role(value):
        return value[:160]
    return ""


def _company_from_title_and_context(title: str, context: dict[str, Any]) -> str:
    title_brand = _brand_from_title(title)
    if title_brand:
        return title_brand

    candidates: list[str] = []
    for key in ("site_name",):
        value = context.get(key)
        if isinstance(value, str) and value:
            candidates.append(value)
    for value in context.get("brand_candidates") or []:
        if isinstance(value, str):
            candidates.append(value)

    parts = [p.strip() for p in re.split(r"[-_|｜—–·]", normalize_text(title)) if p.strip()]
    candidates.extend(parts)
    candidates.append(title)

    for candidate in candidates:
        company = _clean_company_candidate(candidate)
        if company:
            return company
    return ""


def _role_from_title_and_context(title: str, context: dict[str, Any]) -> str:
    for heading in context.get("headings") or []:
        role = _clean_role_candidate(str(heading))
        if role:
            return role
    parts = [p.strip() for p in re.split(r"[-_|｜—–·]", normalize_text(title)) if p.strip()]
    for candidate in parts:
        role = _clean_role_candidate(candidate)
        if role:
            return role
    return _clean_role_candidate(title)


def _detect_page_kind(
    title: str,
    text: str,
    role: str,
    context: dict[str, Any],
    explicit_role: str = "",
) -> str:
    t = normalize_text(title).lower()
    sample = normalize_text("\n".join([title, str(context.get("site_name", "")), text[:12_000]])).lower()
    structured = context.get("job_posting") or {}

    if structured.get("title"):
        return "job_detail"

    login_signals = ["登录", "验证码", "手机号", "密码", "忘记密码"]
    if t in {"登录", "登陆", "login", "sign in", "signin"} or sum(1 for x in login_signals if x.lower() in sample) >= 3:
        return "login"

    campaign_title = bool(
        re.search(r"(?:20)?\d{2}届.*(?:提前批|校园招聘|校招|招聘)", title)
        or re.search(r"(?:校园|秋季|春季|大型|常规).{0,12}招聘项目", title)
    )
    if campaign_title:
        return "campaign"

    career_signals = ["校园招聘", "校招", "招聘官网", "职位列表", "搜索职位", "全部职位", "加入我们", "人才招聘", "招聘职位"]
    if any(x in sample for x in career_signals) and not explicit_role:
        return "career_home"

    if explicit_role or role:
        return "job_detail"
    return "unknown"


def finalize_parsed(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Merge AI output without allowing it to degrade reliable local parsing."""
    merged = dict(base)
    candidate = candidate or {}

    base_company = _clean_company_candidate(str(base.get("company") or ""))
    ai_company = _clean_company_candidate(str(candidate.get("company") or ""))
    if base_company:
        merged["company"] = base_company
    elif ai_company and not _is_placeholder(ai_company):
        merged["company"] = ai_company

    page_kind = str(base.get("page_kind") or "unknown")
    structured = (base.get("_page_context") or {}).get("job_posting") or {}
    base_role = normalize_text(str(base.get("role") or ""))
    ai_role = normalize_text(str(candidate.get("role") or ""))

    if structured.get("title"):
        merged["role"] = normalize_text(str(structured.get("title") or base_role))
    elif page_kind in {"career_home", "campaign"}:
        merged["role"] = "招聘主页"
    elif page_kind == "login":
        merged["role"] = "招聘登录页"
    elif base_role and not _is_placeholder(base_role):
        merged["role"] = base_role
    else:
        clean_ai_role = _clean_role_candidate(ai_role)
        if clean_ai_role:
            merged["role"] = clean_ai_role

    for field in ("location", "deadline", "description", "match_score", "match_reasons", "risks"):
        value = candidate.get(field)
        if value not in (None, "", []):
            merged[field] = value

    try:
        merged["match_score"] = max(0, min(100, int(merged.get("match_score", 0))))
    except Exception:
        merged["match_score"] = int(base.get("match_score", 0) or 0)
    if not isinstance(merged.get("match_reasons"), list):
        merged["match_reasons"] = base.get("match_reasons", [])
    if not isinstance(merged.get("risks"), list):
        merged["risks"] = base.get("risks", [])
    merged["page_kind"] = page_kind
    return merged


def load_profile() -> dict[str, Any]:
    path = PROFILE_PATH if PROFILE_PATH.exists() else PROFILE_EXAMPLE_PATH
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def score_match(text: str, profile: dict[str, Any]) -> tuple[int, list[str], list[str]]:
    haystack = text.lower()
    preferred = profile.get("preferred_keywords") or []
    strong = profile.get("strong_keywords") or []
    avoid = profile.get("avoid_keywords") or []
    cities = profile.get("preferred_cities") or []

    score = 45
    reasons: list[str] = []
    risks: list[str] = []

    strong_hits = [word for word in strong if str(word).lower() in haystack]
    preferred_hits = [word for word in preferred if str(word).lower() in haystack]
    city_hits = [word for word in cities if str(word).lower() in haystack]
    avoid_hits = [word for word in avoid if str(word).lower() in haystack]

    if strong_hits:
        score += min(30, 12 + 6 * len(strong_hits))
        reasons.append("强匹配关键词：" + "、".join(strong_hits[:4]))
    if preferred_hits:
        score += min(20, 4 * len(preferred_hits))
        reasons.append("方向相关：" + "、".join(preferred_hits[:5]))
    if city_hits:
        score += 5
        reasons.append("地点偏好匹配：" + "、".join(city_hits[:2]))
    if avoid_hits:
        score -= min(35, 18 * len(avoid_hits))
        risks.append("出现规避关键词：" + "、".join(avoid_hits[:3]))

    if not reasons:
        reasons.append("暂未发现明显的强匹配关键词，建议人工快速确认")
    if "经验" in haystack and ("3年" in haystack or "三年" in haystack or "5年" in haystack or "五年" in haystack):
        score -= 10
        risks.append("可能存在工作年限要求")

    return max(0, min(100, score)), reasons, risks


def heuristic_parse(
    *,
    url: str,
    title: str,
    text: str,
    source_type: str,
    page_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = normalize_text(text)[:120_000]
    context = page_context or {}
    structured = context.get("job_posting") if isinstance(context.get("job_posting"), dict) else {}
    adapted = apply_site_adapter(url=url, title=title, text=text, context=context)
    adapter_fields = adapted.get("fields") or {}

    company = normalize_text(str(structured.get("company") or adapter_fields.get("company") or ""))
    structured_role = normalize_text(str(structured.get("title") or adapter_fields.get("role") or ""))
    location = normalize_text(str(structured.get("location") or adapter_fields.get("location") or ""))
    deadline = normalize_text(str(structured.get("deadline") or adapter_fields.get("deadline") or ""))

    company = company or _first_match(FIELD_PATTERNS["company"], text)
    explicit_role = _first_match(FIELD_PATTERNS["role"], text)
    location = location or _first_match(FIELD_PATTERNS["location"], text)
    deadline = deadline or _first_match(DATE_PATTERNS, text)

    company = _clean_company_candidate(company) or _company_from_title_and_context(title, context)
    role = ""
    for labeled_role in (structured_role, explicit_role):
        candidate = normalize_text(labeled_role).strip("-_|｜—–· ")
        if candidate and candidate.lower() not in NOISE_EXACT and not any(candidate == phrase for phrase in NOISE_ROLE_PHRASES):
            role = candidate[:160]
            break
    role = role or _role_from_title_and_context(title, context)

    page_kind = adapted.get("page_kind_hint") or _detect_page_kind(title, text, role, context, explicit_role=_clean_role_candidate(explicit_role))
    if page_kind in {"career_home", "campaign"}:
        role = "招聘主页"
    elif page_kind == "login":
        role = "招聘登录页"
    elif not role:
        role = "待识别岗位"

    profile = load_profile()
    score_text = "\n".join([title, company, role, location, context.get("main_text", "")[:20_000], text[:30_000]])
    score, reasons, risks = score_match(score_text, profile)

    if page_kind in {"career_home", "campaign"}:
        score = max(0, score - 8)
        risks.insert(0, "当前页面更像招聘主页/校招专题，不是单个职位详情；进入具体岗位后再保存，岗位识别会更准确")
    elif page_kind == "login":
        score = max(0, score - 20)
        risks.insert(0, "当前页面是登录页；登录后进入具体岗位详情页再保存")
    elif page_kind == "unknown" and role == "待识别岗位":
        risks.insert(0, "没有识别到明确岗位；建议进入职位详情页，或手动修正")

    if not company:
        risks.append("没有可靠识别到公司名称，可用“修正信息”手动补充")

    description = normalize_text(str(context.get("main_text") or "")) or text
    result = {
        "source_url": url,
        "source_type": source_type,
        "title": title[:200],
        "company": company[:120],
        "role": role[:160],
        "location": location[:120],
        "deadline": deadline[:80],
        "description": description[:8000],
        "raw_text": text,
        "match_score": score,
        "match_reasons": reasons,
        "risks": risks,
        "status": "inbox",
        "page_kind": page_kind,
        "adapter_name": str(adapted.get("adapter_name") or "通用网页"),
        "page_context": context,
        "_page_context": context,
    }
    return result


async def fetch_page(url: str) -> tuple[str, str, dict[str, Any]]:
    safe_url = validate_public_http_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36 JobPilot/0.1.3",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
    }
    timeout = httpx.Timeout(18.0, connect=8.0)
    async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers) as client:
        response = await client.get(safe_url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "html" not in content_type and "text" not in content_type:
            raise ValueError("这个链接不是可直接解析的网页；请用浏览器扩展保存当前页面，或粘贴招聘文字")
        return extract_page(response.text)
