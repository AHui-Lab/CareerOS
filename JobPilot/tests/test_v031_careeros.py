from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CareerOsLauncherContractTests(unittest.TestCase):
    def test_unified_launcher_checks_both_services_and_does_not_kill_unknown_ports(self):
        ps1 = (ROOT / "career-os.ps1").read_text(encoding="utf-8")
        self.assertIn("8766", ps1)
        self.assertIn("8765", ps1)
        self.assertIn("'CareerVault'", ps1)
        self.assertIn("CareerOS will not terminate it", ps1)
        self.assertNotIn("Stop-Process", ps1)
        self.assertIn("Start-Process 'http://127.0.0.1:8765'", ps1)

    def test_bat_entrypoint_exists(self):
        bat = (ROOT / "career-os.bat").read_text(encoding="utf-8")
        self.assertIn("career-os.ps1", bat)

    def test_version_consistency_is_031(self):
        init = (ROOT / "jobpilot" / "__init__.py").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "extension" / "manifest.json").read_text(encoding="utf-8"))
        html = (ROOT / "jobpilot" / "static" / "index.html").read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "0.3.1")
        self.assertEqual(manifest["version"], "0.3.1")
        self.assertIn("V0.3.1", html)


if __name__ == "__main__":
    unittest.main()
