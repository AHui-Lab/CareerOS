from __future__ import annotations

import json
from urllib import request


class CareerVaultClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8766", timeout: float = 3.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _json(self, path: str, method: str = "GET", payload: dict | None = None):
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def health(self) -> dict:
        return self._json("/api/health")

    def profile(self) -> dict:
        return self._json("/api/jobpilot/profile")

    def experiences(self, resume_ready: bool = True) -> list[dict]:
        value = "true" if resume_ready else "false"
        return self._json(f"/api/jobpilot/experiences?resume_ready={value}")

    def context_for_jd(self, jd: str, limit: int = 6) -> dict:
        return self._json("/api/jobpilot/context", method="POST", payload={"jd": jd, "limit": limit})
