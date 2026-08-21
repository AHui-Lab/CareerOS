from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExtensionCompatibilityContractTests(unittest.TestCase):
    def test_extension_does_not_hard_fail_on_exact_backend_version(self):
        popup = (ROOT / "extension" / "popup.js").read_text(encoding="utf-8")
        self.assertIn("chrome.runtime.getManifest().version", popup)
        self.assertNotIn("EXPECTED_VERSION", popup)
        self.assertNotIn("扩展需要 ${EXPECTED_VERSION}", popup)
        self.assertIn("接口可用，继续运行", popup)

    def test_extension_preserves_full_page_url_in_context(self):
        popup = (ROOT / "extension" / "popup.js").read_text(encoding="utf-8")
        self.assertIn("page_url:pageUrl", popup)
        self.assertIn("url:pageUrl", popup)


if __name__ == "__main__":
    unittest.main()
