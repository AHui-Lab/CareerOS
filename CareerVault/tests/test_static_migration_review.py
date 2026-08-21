import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "careervault" / "static" / "migration-review.js"
INDEX = ROOT / "careervault" / "static" / "index.html"


class MigrationReviewStaticTests(unittest.TestCase):
    def test_dashboard_decoration_is_idempotent(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("if (card.innerHTML !== nextHtml)", text)
        self.assertIn("requestAnimationFrame", text)

    def test_migration_script_is_cache_busted(self):
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn("migration-review.js?v=", html)


if __name__ == "__main__":
    unittest.main()
