from __future__ import annotations

import json
import unittest
import warnings
from contextlib import contextmanager, ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from jobpilot import db, interview_prep, sync


@unittest.skipUnless(sync.CRYPTO_AVAILABLE, "同步加密依赖未安装")
class InterviewPrepSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle = self.root / "bundled"
        folder = self.bundle / "example-role"
        folder.mkdir(parents=True)
        workspace = {
            "id": "example-role", "title": "示例公司 · 嵌入式", "team": "开发团队",
            "date_window": "时间待确认", "summary": "重点准备驱动通信",
            "documents": [{"id": "guide", "title": "准备资料"}],
            "tasks": [{"id": "review", "date": "2026-10-09", "text": "复习通信"}],
            "defaults": {"interview_date": "", "location": "", "jd": "岗位原始 JD",
                         "questions": "", "notes": "", "completed": [], "sources": []}}
        (folder / "workspace.json").write_text(json.dumps(workspace, ensure_ascii=False), encoding="utf-8")
        (folder / "guide.md").write_text("# 准备资料\n\n通信与驱动。", encoding="utf-8")
        app = FastAPI()
        interview_prep.register_routes(app)
        self.client = TestClient(app)

    @contextmanager
    def device(self, name: str, bundle: Path | None = None):
        data = self.root / name
        data.mkdir(exist_ok=True)
        database = data / "jobpilot.db"
        if not database.exists():
            database.write_bytes(f"isolated database for {name}".encode())
        private = data / "private"
        private.mkdir(exist_ok=True)
        (private / "sync-passphrase").write_text("test-only-passphrase", encoding="utf-8")
        with ExitStack() as stack:
            for obj, attr, value in [
                (db, "DATA_DIR", data), (db, "DB_PATH", database), (db, "BACKUP_DIR", data / "backups"),
                (sync, "SYNC_DIR", data / "sync-repo"), (sync, "CONFIG_PATH", private / "sync-config.json"),
                (sync, "PASSPHRASE_PATH", private / "sync-passphrase"),
                (sync, "VAULT_ROOT", data / "vault"), (sync, "VAULT_PRIVATE", data / "vault-private"),
                (interview_prep, "PREP_ROOT", bundle or self.bundle)]:
                stack.enter_context(patch.object(obj, attr, value))
            stack.enter_context(patch.object(db, "backup_database", return_value=None))
            stack.enter_context(patch.object(db, "data_status", return_value={}))
            stack.enter_context(patch.object(db, "init_db", return_value=None))
            # The encrypted snapshot and restore are real; remote Git calls stay local to the test.
            stack.enter_context(patch.object(sync, "_ensure_repo", return_value=None))
            stack.enter_context(patch.object(sync, "_git", return_value="test-head"))
            if not sync.CONFIG_PATH.exists():
                sync._write_config({"remote_url": "test-local-repo", "branch": "main"})
            yield data

    def accept_payload(self, payload: bytes):
        sync.SYNC_DIR.mkdir(exist_ok=True)
        (sync.SYNC_DIR / sync.ARCHIVE_NAME).write_bytes(payload)
        return sync.accept()

    def test_encrypted_snapshot_restores_all_preparation_on_computer_without_bundled_docs(self):
        with self.device("sender"):
            self.client.patch("/api/interview-prep/example-role/notes", json={
                "revision": 0, "notes": "我的准备笔记", "completed": ["review"],
                "sources": [{"title": "可信来源", "url": "https://example.com/guide", "note": "收集结论"}]})
            created = self.client.post("/api/interview-prep", json={"company": "另一公司", "role": "算法", "jd": "新岗位 JD"}).json()
            custom_id = created["workspace"]["id"]
            self.client.patch(f"/api/interview-prep/{custom_id}/notes", json={"revision": 0, "notes": "另一个岗位的笔记"})
            payload = sync._make_archive()
            self.assertTrue(payload.startswith(b"CAREEROS-SYNC-V1\n"))
            self.assertNotIn("我的准备笔记".encode(), payload)
            sync._unpack_archive(payload, self.root / "inspection")
            content = self.root / "inspection" / "content"
            self.assertTrue((content / "private/interview-prep/materials/example-role/workspace.json").is_file())
            self.assertFalse((content / "private/sync-passphrase").exists())
            self.assertFalse((content / "private/sync-config.json").exists())
        with self.device("receiver", self.root / "no-local-docs"):
            self.accept_payload(payload)
            items = self.client.get("/api/interview-prep").json()["items"]
            self.assertEqual({item["id"] for item in items}, {"example-role", custom_id})
            notes = self.client.get("/api/interview-prep/example-role").json()["notes"]
            self.assertEqual(notes["notes"], "我的准备笔记")
            self.assertEqual(notes["completed"], ["review"])
            self.assertEqual(notes["sources"][0]["note"], "收集结论")
            document = self.client.get("/api/interview-prep/example-role/documents/guide")
            self.assertEqual(document.json()["content"], "# 准备资料\n\n通信与驱动。")
            self.assertEqual(self.client.get("/api/interview-prep/example-role/documents/guide/download").status_code, 200)
            self.assertEqual(self.client.get(f"/api/interview-prep/{custom_id}").json()["notes"]["notes"], "另一个岗位的笔记")
            # A second sync from this computer must retain the restored material.
            repeated = sync._make_archive()
            sync._unpack_archive(repeated, self.root / "repeated")
            self.assertEqual((self.root / "repeated/content/private/interview-prep/materials/example-role/guide.md").read_text(encoding="utf-8"), document.json()["content"])

    def test_synced_material_overrides_older_bundled_copy_and_is_not_duplicated(self):
        with self.device("sender"):
            material = interview_prep._synced_materials_root() / "example-role"
            material.mkdir(parents=True)
            (material / "workspace.json").write_bytes((self.bundle / "example-role/workspace.json").read_bytes())
            (material / "guide.md").write_text("# 新版资料", encoding="utf-8")
            self.assertEqual(self.client.get("/api/interview-prep/example-role/documents/guide").json()["content"], "# 新版资料")
            # ZipFile emits UserWarning on duplicate entries.
            with warnings.catch_warnings():
                warnings.simplefilter("error", UserWarning)
                payload = sync._make_archive()
            sync._unpack_archive(payload, self.root / "inspection")
            self.assertEqual((self.root / "inspection/content/private/interview-prep/materials/example-role/guide.md").read_text(encoding="utf-8"), "# 新版资料")

    def test_rollback_restores_local_material_and_removes_imported_workspaces(self):
        with self.device("sender"):
            custom_id = self.client.post("/api/interview-prep", json={"company": "远程公司", "role": "测试"}).json()["workspace"]["id"]
            (self.bundle / "example-role/guide.md").write_text("# 远程资料", encoding="utf-8")
            payload = sync._make_archive()
        (self.bundle / "example-role/guide.md").write_text("# 本机原资料", encoding="utf-8")
        with self.device("receiver"):
            self.client.patch("/api/interview-prep/example-role/notes", json={"revision": 0, "notes": "本机原笔记"})
            self.accept_payload(payload)
            self.assertEqual(self.client.get("/api/interview-prep/example-role/documents/guide").json()["content"], "# 远程资料")
            sync.rollback()
            self.assertEqual(self.client.get("/api/interview-prep/example-role/documents/guide").json()["content"], "# 本机原资料")
            self.assertEqual(self.client.get("/api/interview-prep/example-role").json()["notes"]["notes"], "本机原笔记")
            self.assertEqual(self.client.get(f"/api/interview-prep/{custom_id}").status_code, 404)


if __name__ == "__main__":
    unittest.main()
