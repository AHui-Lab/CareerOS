import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from jobpilot.main import OpportunityReview, _job_url_from_text, _opportunity_preview, autofill_package, parse_and_store
from jobpilot import db


class ImportReviewTests(unittest.IsolatedAsyncioTestCase):
    def test_text_import_recovers_labeled_job_link(self):
        self.assertEqual(_job_url_from_text("职位链接：https://jobs.example.com/123。"), "https://jobs.example.com/123")
        self.assertEqual(_job_url_from_text("公司官网 https://example.com"), "")

    def test_preview_reports_existing_link_and_non_job_page(self):
        draft = {"company": "示例公司", "role": "招聘主页", "description": "网页正文", "page_kind": "career_home"}
        with patch("jobpilot.main.heuristic_parse", return_value=draft), patch("jobpilot.main.db.find_by_url", return_value={"id": 12, "company": "旧公司", "role": "旧岗位"}):
            result = _opportunity_preview(url="https://example.com/jobs", title="招聘", text="岗位列表", source_type="browser")
        self.assertEqual(result["existing"]["id"], 12)
        self.assertEqual(result["draft"]["jd_text"], "网页正文")
        self.assertTrue(result["warning"])

    async def test_reviewed_fields_win_and_refresh_keeps_existing_status(self):
        base = {"company": "误识别", "role": "招聘主页", "status": "inbox", "description": "旧 JD"}
        review = OpportunityReview(company="正确公司", role="嵌入式工程师", jd_text="人工确认 JD")
        with patch("jobpilot.main.db.find_by_url", return_value={"id": 7, "status": "interview"}), \
             patch("jobpilot.main.heuristic_parse", return_value=base), \
             patch("jobpilot.main.enrich_with_ai", new_callable=AsyncMock, return_value={}), \
             patch("jobpilot.main.finalize_parsed", return_value=base.copy()), \
             patch("jobpilot.main.db.refresh_opportunity", return_value={"id": 7}) as refresh, \
             patch("jobpilot.main.db.edit_opportunity", return_value={"id": 7, "company": "正确公司", "role": "嵌入式工程师", "jd_text": "人工确认 JD", "status": "interview"}) as edit, \
             patch("jobpilot.main.opportunity_ai_enabled", return_value=False):
            result = await parse_and_store(url="https://example.com/job/7", title="招聘", text="招聘信息", source_type="browser", refresh_existing=True, review=review)
        self.assertTrue(result["refreshed"])
        self.assertEqual(result["item"]["status"], "interview")
        self.assertEqual(refresh.call_args.kwargs["preserve_status"], True)
        self.assertEqual(refresh.call_args.args[1]["company"], "正确公司")
        self.assertEqual(edit.call_args.args[1]["jd_text"], "人工确认 JD")


class AutofillVersionTests(unittest.IsolatedAsyncioTestCase):
    async def test_base_only_does_not_choose_unrelated_latest_resume(self):
        with patch("jobpilot.main.db.latest_resume_version") as latest, \
             patch("jobpilot.main.db.get_profile", return_value={}), \
             patch("jobpilot.main.build_flat_package", return_value={}), \
             patch("jobpilot.main.build_structured_autofill", return_value={}), \
             patch("jobpilot.main._best_role_field_set", return_value=None):
            result = await autofill_package(base_only=True)
        latest.assert_not_called()
        self.assertIsNone(result["resume_version"])


class NextActionPersistenceTests(unittest.TestCase):
    def test_next_action_survives_edit_and_reload(self):
        with TemporaryDirectory() as folder, patch.object(db, "DB_PATH", Path(folder) / "jobpilot.db"), patch.object(db, "_copy_legacy_database_if_needed", return_value=False):
            db.init_db()
            item = db.insert_opportunity({"company": "示例公司", "role": "嵌入式工程师", "status": "preparing"})
            db.edit_opportunity(item["id"], {"next_action": "完善项目经历", "next_action_at": "2026-10-01"})
            loaded = db.get_opportunity(item["id"])
            self.assertEqual(loaded["next_action"], "完善项目经历")
            self.assertEqual(loaded["next_action_at"], "2026-10-01")


if __name__ == "__main__":
    unittest.main()
