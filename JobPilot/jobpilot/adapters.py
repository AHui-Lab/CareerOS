from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


def _clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\u00a0", " ").split()).strip()


@dataclass(frozen=True)
class AdapterSpec:
    key: str
    label: str
    hosts: tuple[str, ...]
    markers: tuple[str, ...] = ()


ADAPTERS: tuple[AdapterSpec, ...] = (
    AdapterSpec("moka", "Moka", ("mokahr.com",), ("moka", "campus_apply", "social_apply")),
    AdapterSpec("beisen", "北森 / iTalent", ("italent.cn", "beisen.com"), ("italent", "beisen")),
    AdapterSpec("nowcoder", "牛客招聘", ("nowcoder.com",), ("nowcoder", "牛客")),
)


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "company": (
        "company", "company_name", "employer", "organization", "hiringorganization",
        "公司", "公司名称", "招聘单位", "单位名称", "企业名称", "雇主名称",
    ),
    "role": (
        "role", "job", "job_title", "jobtitle", "position", "position_name", "title",
        "职位", "职位名称", "岗位", "岗位名称", "招聘岗位", "应聘岗位", "应聘职位",
    ),
    "location": (
        "location", "job_location", "city", "workplace", "work_location",
        "工作地点", "工作城市", "办公地点", "工作地址", "城市", "地点",
    ),
    "deadline": (
        "deadline", "validthrough", "apply_deadline", "application_deadline",
        "截止", "截止时间", "截止日期", "申请截止", "投递截止", "网申截止", "报名截止",
    ),
}


def _normalize_key(key: Any) -> str:
    value = _clean(key).lower().replace("：", "").replace(":", "")
    return "".join(ch for ch in value if not ch.isspace() and ch not in "_-./")


def _pick_labeled(context: dict[str, Any], field: str) -> str:
    labeled = context.get("labeled_fields") or {}
    if not isinstance(labeled, dict):
        return ""
    aliases = {_normalize_key(x) for x in FIELD_ALIASES[field]}
    for key, value in labeled.items():
        if _normalize_key(key) in aliases:
            candidate = _clean(value)
            if candidate:
                return candidate
    return ""


def detect_adapter(url: str, context: dict[str, Any] | None = None) -> AdapterSpec:
    context = context or {}
    host = _clean(context.get("hostname")).lower()
    if not host:
        try:
            host = (urlparse(url).hostname or "").lower()
        except Exception:
            host = ""
    hint = _clean(context.get("adapter_hint")).lower()
    title = _clean(context.get("site_name")).lower()
    sample = " ".join((host, hint, title))

    for spec in ADAPTERS:
        if any(host == domain or host.endswith("." + domain) for domain in spec.hosts):
            return spec
        if any(marker.lower() in sample for marker in spec.markers):
            return spec
    return AdapterSpec("generic", "通用网页", ())


def _page_kind_hint(url: str, role: str, context: dict[str, Any], adapter: AdapterSpec) -> str:
    path = _clean(context.get("pathname"))
    if not path:
        try:
            path = urlparse(url).path
        except Exception:
            path = ""
    path_l = path.lower()
    role = _clean(role)

    if context.get("job_posting") and isinstance(context.get("job_posting"), dict):
        if _clean(context["job_posting"].get("title")):
            return "job_detail"

    detail_tokens = ("/job/", "/jobs/", "jobdetail", "job-detail", "positiondetail", "position-detail", "/position/", "/positions/")
    if role and any(token in path_l for token in detail_tokens):
        return "job_detail"

    if adapter.key == "moka":
        if any(token in path_l for token in ("campus_apply", "social_apply")) and role:
            return "job_detail"
        if any(token in path_l for token in ("campus", "jobs", "positions")):
            return "career_home"
    elif adapter.key == "beisen":
        if role and any(token in path_l for token in ("job", "position", "detail")):
            return "job_detail"
    elif adapter.key == "nowcoder":
        if role and any(token in path_l for token in ("job", "position", "detail")):
            return "job_detail"

    return ""


def apply_site_adapter(
    *,
    url: str,
    title: str,
    text: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return adapter metadata and high-confidence DOM fields.

    The browser extension collects label/value pairs from the rendered DOM.  This
    module centralises ATS-specific detection so new platforms can be added
    without changing the main parser.
    """
    context = context or {}
    adapter = detect_adapter(url, context)

    fields = {
        "company": _pick_labeled(context, "company"),
        "role": _pick_labeled(context, "role"),
        "location": _pick_labeled(context, "location"),
        "deadline": _pick_labeled(context, "deadline"),
    }

    # Adapter-provided fields from the extension are even more direct than the
    # generic label scanner.  Keep this small and explicit.
    browser_fields = context.get("adapter_fields") or {}
    if isinstance(browser_fields, dict):
        for key in fields:
            candidate = _clean(browser_fields.get(key))
            if candidate:
                fields[key] = candidate

    return {
        "adapter_key": adapter.key,
        "adapter_name": adapter.label,
        "fields": fields,
        "page_kind_hint": _page_kind_hint(url, fields.get("role", ""), context, adapter),
    }
