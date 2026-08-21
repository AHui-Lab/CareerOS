import unittest

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


if __name__ == "__main__":
    unittest.main()
