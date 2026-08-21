from __future__ import annotations

import sqlite3
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from jobpilot.main import _decorate_opportunities, _recover_source_url, app
from jobpilot import opportunity_meta


class OpportunityLinkRecoveryTests(unittest.TestCase):
    def test_keeps_direct_source_url(self):
        item = {"source_url": "https://jobs.example.com/job/123", "page_context": {"hostname": "ignored.example"}}
        self.assertEqual(_recover_source_url(item), "https://jobs.example.com/job/123")

    def test_recovers_url_from_page_context(self):
        item = {"source_url": "", "page_context": {"hostname": "jobs.example.com", "pathname": "/position/abc"}}
        self.assertEqual(_recover_source_url(item), "https://jobs.example.com/position/abc")

    def test_prefers_full_context_url_when_available(self):
        item = {"source_url": "", "page_context": {"page_url": "https://jobs.example.com/position/abc?campus=1", "hostname": "jobs.example.com", "pathname": "/position/abc"}}
        self.assertEqual(_recover_source_url(item), "https://jobs.example.com/position/abc?campus=1")

    def test_decorates_category_and_recovered_link(self):
        rows = [{"id": 7, "source_url": "", "page_context": {"hostname": "jobs.example.com", "pathname": "/7"}}]
        with patch("jobpilot.main.get_category_map", return_value={7: "ai"}):
            out = _decorate_opportunities(rows)
        self.assertEqual(out[0]["job_category"], "ai")
        self.assertEqual(out[0]["source_url"], "https://jobs.example.com/7")


class OpportunityCategoryPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.conn = sqlite3.connect(Path(self.tmp.name) / "meta.db")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE opportunities (id INTEGER PRIMARY KEY);
            INSERT INTO opportunities(id) VALUES (1);
            """
        )

        @contextmanager
        def fake_connect():
            try:
                yield self.conn
                self.conn.commit()
            except Exception:
                self.conn.rollback()
                raise

        self.connect_patch = patch("jobpilot.opportunity_meta.db.connect", side_effect=fake_connect)
        self.get_patch = patch("jobpilot.opportunity_meta.db.get_opportunity", side_effect=lambda oid: {"id": oid} if oid == 1 else None)
        self.connect_patch.start()
        self.get_patch.start()
        opportunity_meta.init_opportunity_meta()

    def tearDown(self):
        self.connect_patch.stop()
        self.get_patch.stop()
        self.conn.close()
        self.tmp.cleanup()

    def test_category_round_trip(self):
        saved = opportunity_meta.set_category(1, "semiconductor")
        self.assertEqual(saved["job_category"], "semiconductor")
        self.assertEqual(opportunity_meta.get_category_map(), {1: "semiconductor"})

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            opportunity_meta.set_category(1, "made-up")


class OpportunityUiContractTests(unittest.TestCase):
    def test_category_route_is_available(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/opportunities/{opportunity_id}/category", paths)

    def test_static_ui_contains_required_filters(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "jobpilot" / "static" / "index.html").read_text(encoding="utf-8")
        js = (root / "jobpilot" / "static" / "app.js").read_text(encoding="utf-8")
        for marker in ("data-memo-scope=\"all\"", "data-memo-scope=\"unsubmitted\"", "data-memo-scope=\"submitted\"", "memoCategoryFilter", "memoStatusFilter"):
            self.assertIn(marker, html)
        self.assertIn("SUBMITTED_STATUSES", js)
        self.assertIn("UNSUBMITTED_STATUSES", js)
        self.assertIn("job-category", js)


if __name__ == "__main__":
    unittest.main()
