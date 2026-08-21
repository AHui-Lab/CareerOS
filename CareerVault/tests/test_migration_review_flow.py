from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from careervault.main import _jobpilot_eligible, app
from careervault.migration_review import complete_migration_review
from careervault.store import dump_frontmatter, split_frontmatter


class MigrationReviewFlowTests(unittest.TestCase):
    def test_pending_migration_is_never_jobpilot_eligible(self):
        item = {"resume_ready": True, "migration_review": "required"}
        self.assertFalse(_jobpilot_eligible(item))
        self.assertTrue(_jobpilot_eligible({"resume_ready": True, "migration_review": "completed"}))
        self.assertFalse(_jobpilot_eligible({"resume_ready": False, "migration_review": "completed"}))

    def test_complete_review_updates_frontmatter_and_preserves_body(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiences = root / "experiences"
            target = experiences / "legacy-project" / "index.md"
            target.parent.mkdir(parents=True)
            meta = {
                "schema_version": 1,
                "id": "legacy-project",
                "type": "project",
                "title": "Legacy Project",
                "status": "draft",
                "resume_ready": False,
                "migration_review": "required",
                "created_at": "2026-08-21T10:00:00+08:00",
                "updated_at": "2026-08-21T10:00:00+08:00",
            }
            body = "# Legacy Project\n\n## 项目概述\n保留正文。\n\n## 事实记录\n事实 A。\n\n## 量化成果\n\n## Notes\n"
            target.write_text(dump_frontmatter(meta, body), encoding="utf-8")

            with (
                patch("careervault.migration_review.EXPERIENCES", experiences),
                patch("careervault.store.EXPERIENCES", experiences),
                patch("careervault.store.ROOT", root),
            ):
                result = complete_migration_review("legacy-project", resume_ready=True)

            saved_meta, saved_body = split_frontmatter(target.read_text(encoding="utf-8"))
            self.assertEqual(saved_meta["migration_review"], "completed")
            self.assertIn("migration_reviewed_at", saved_meta)
            self.assertEqual(saved_meta["status"], "verified")
            self.assertTrue(saved_meta["resume_ready"])
            self.assertIn("事实 A。", saved_body)
            self.assertEqual(result["migration_review"], "completed")

    def test_review_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/experiences/{experience_id}/migration-review", paths)

    def test_ui_contains_explicit_review_action(self):
        root = Path(__file__).resolve().parents[1]
        js = (root / "careervault" / "static" / "migration-review.js").read_text(encoding="utf-8")
        self.assertIn("确认事实无误，完成迁移审核", js)
        self.assertIn("data-complete-migration-review", js)
        self.assertIn("可用于简历生成", js)


if __name__ == "__main__":
    unittest.main()
