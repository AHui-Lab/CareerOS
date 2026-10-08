from __future__ import annotations

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from jobpilot import interview_prep


class InterviewPrepTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_patch = patch.object(interview_prep.db, "DATA_DIR", Path(self.tmp.name))
        self.data_patch.start()
        self.addCleanup(self.data_patch.stop)
        app = FastAPI()
        app.include_router(interview_prep.router)
        self.client = TestClient(app)
        self.base = "/api/interview-prep/sany-bms-202610"

    def test_curated_documents_available_and_paths_restricted(self):
        response = self.client.get(self.base)
        self.assertEqual(response.status_code, 200)
        workspace = response.json()["workspace"]
        for document in workspace["documents"]:
            result = self.client.get(f"{self.base}/documents/{document['id']}")
            self.assertEqual(result.status_code, 200)
            self.assertTrue(result.json()["content"].startswith("# "))
        self.assertEqual(self.client.get(f"{self.base}/documents/workspace").status_code, 404)
        self.assertEqual(self.client.get("/api/interview-prep/unknown").status_code, 404)

    def test_save_roundtrip_preserves_jd_and_writes_private_file(self):
        initial = self.client.get(self.base).json()["notes"]
        response = self.client.patch(f"{self.base}/notes", json={"revision": 0, "notes": "中文测试笔记", "completed": ["can"]})
        self.assertEqual(response.status_code, 200)
        stored = self.client.get(self.base).json()["notes"]
        self.assertEqual(stored["notes"], "中文测试笔记")
        self.assertEqual(stored["completed"], ["can"])
        self.assertEqual(stored["jd"], initial["jd"])
        self.assertEqual(stored["revision"], 1)
        self.assertTrue((Path(self.tmp.name) / "private/interview-prep/sany-bms-202610.json").is_file())

    def test_stale_update_does_not_overwrite_notes(self):
        self.client.patch(f"{self.base}/notes", json={"revision": 0, "notes": "第一个窗口"})
        response = self.client.patch(f"{self.base}/notes", json={"revision": 0, "notes": "第二个窗口"})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get(self.base).json()["notes"]["notes"], "第一个窗口")

    def test_rejects_unsafe_sources_invalid_dates_and_unknown_tasks(self):
        payloads = [
            {"sources": [{"title": "bad", "url": "javascript:alert(1)"}]},
            {"interview_date": "2026-02-30"},
            {"completed": ["invented"]},
        ]
        for payload in payloads:
            self.assertEqual(self.client.patch(f"{self.base}/notes", json={"revision": 0, **payload}).status_code, 422)
        self.assertEqual(self.client.get(self.base).json()["notes"]["revision"], 0)

    def test_multiple_workspaces_persist_and_keep_notes_separate(self):
        created = []
        for company, role in [("公司甲", "嵌入式"), ("公司乙", "算法")]:
            response = self.client.post("/api/interview-prep", json={
                "company": company, "role": role, "jd": f"{role} JD", "interview_date": "2026-10-15"})
            self.assertEqual(response.status_code, 201)
            created.append(response.json()["workspace"]["id"])
        self.assertNotEqual(*created)
        first, second = [f"/api/interview-prep/{key}" for key in created]
        self.assertEqual(self.client.patch(first + "/notes", json={
            "revision": 0, "notes": "甲的准备", "interview_date": "2026-10-16"}).status_code, 200)
        self.assertEqual(self.client.get(second).json()["notes"]["notes"], "")
        self.assertEqual(self.client.get(second).json()["notes"]["jd"], "算法 JD")
        self.assertEqual(self.client.get(self.base).json()["notes"]["revision"], 0)
        items = {item["id"]: item for item in self.client.get("/api/interview-prep").json()["items"]}
        self.assertTrue(set(created + ["sany-bms-202610"]).issubset(items))
        self.assertEqual(items[created[0]]["interview_date"], "2026-10-16")
        self.assertTrue(items[created[0]]["updated_at"])
        # A fresh app sees both workspaces and the independently saved notes.
        app = FastAPI()
        interview_prep.register_routes(app)
        fresh = TestClient(app)
        self.assertEqual(fresh.get(first).json()["notes"]["notes"], "甲的准备")
        self.assertEqual(fresh.get(second).json()["workspace"]["title"], "公司乙 · 算法")
        self.assertEqual(fresh.post("/api/interview-prep", json={"company": "公司丙", "role": "测试"}).status_code, 201)

    def test_new_curated_workspaces_are_discovered_without_code_changes(self):
        workspace = self.client.get(self.base).json()["workspace"]
        workspace.update(id="another-role", title="另一公司 · 软件", defaults={
            "interview_date": "", "location": "", "jd": "", "questions": "", "notes": "", "completed": [], "sources": []})
        root = Path(self.tmp.name) / "curated"
        folder = root / "another-role"
        folder.mkdir(parents=True)
        (folder / "workspace.json").write_text(json.dumps(workspace), encoding="utf-8")
        with patch.object(interview_prep, "PREP_ROOT", root):
            items = self.client.get("/api/interview-prep").json()["items"]
            self.assertEqual([item["id"] for item in items], ["another-role"])
            self.assertEqual(self.client.get("/api/interview-prep/another-role").status_code, 200)

    def test_create_rejects_blank_names_and_invalid_dates(self):
        for payload in [{"company": " ", "role": "工程师"}, {"company": "公司", "role": " "},
                        {"company": "公司", "role": "工程师", "interview_date": "2026-02-30"}]:
            self.assertEqual(self.client.post("/api/interview-prep", json=payload).status_code, 422)
        self.assertFalse(interview_prep._custom_root().exists())


if __name__ == "__main__":
    unittest.main()
