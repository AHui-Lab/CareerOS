from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    pass


def validate_public_http_url(url: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("只支持 http:// 或 https:// 招聘链接")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise UnsafeUrlError("不能抓取本机或局域网地址")

    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeUrlError("无法解析这个网址的域名") from exc

    for info in addr_info:
        raw_ip = info[4][0]
        ip = ipaddress.ip_address(raw_ip)
        if not ip.is_global:
            raise UnsafeUrlError("出于安全原因，不能抓取内网、环回或保留地址")
    return url
