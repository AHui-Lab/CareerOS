import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch

from careervault import store


class StoreTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(store.slugify("JobPilot 求职助手"), "jobpilot-求职助手")

    def test_frontmatter_roundtrip(self):
        text = store.dump_frontmatter({"id": "x", "skills": ["Python"]}, "# X\n")
        meta, body = store.split_frontmatter(text)
        self.assertEqual(meta["id"], "x")
        self.assertIn("# X", body)

    def test_yaml_date_like_values_stay_strings(self):
        text = "---\nid: x\nupdated_at: 2026-08-21\nstart: 2024-09-01\n---\n# X\n"
        meta, _ = store.split_frontmatter(text)
        self.assertIsInstance(meta["updated_at"], str)
        self.assertEqual(meta["updated_at"], "2026-08-21")
        self.assertIsInstance(meta["start"], str)
        self.assertEqual(meta["start"], "2024-09-01")

    def test_tokenize(self):
        tokens = store.tokenize("Python FastAPI 多传感器融合")
        self.assertIn("python", tokens)
        self.assertTrue(any("传感" in x or "感器" in x for x in tokens))

    def test_typed_record_and_links_roundtrip(self):
        with TemporaryDirectory() as tmp:
            experiences = Path(tmp) / "experiences"
            with patch.object(store, "EXPERIENCES", experiences), patch.object(store, "ROOT", Path(tmp)):
                project = store.create_experience({"title": "智能车项目", "type": "project"})
                patent = store.create_experience({
                    "title": "检测装置专利", "type": "patent",
                    "related_experience_ids": [project["id"]],
                    "details": {"patent_status": "已公开", "patent_number": "CN123"},
                })
                loaded = store.get_experience(patent["id"])
                self.assertEqual(loaded["type"], "patent")
                self.assertEqual(loaded["related_experience_ids"], [project["id"]])
                self.assertEqual(loaded["details"]["patent_number"], "CN123")


if __name__ == "__main__":
    unittest.main()
