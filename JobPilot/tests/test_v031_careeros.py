from pathlib import Path
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
        self.assertIn("version mismatch", ps1)
        self.assertIn('Start-Process $appUrl', ps1)

    def test_bat_entrypoint_exists(self):
        bat = (ROOT / "career-os.bat").read_text(encoding="utf-8")
        self.assertIn("career-os.ps1", bat)

    def test_ui_version_matches_backend_version(self):
        init = (ROOT / "jobpilot" / "__init__.py").read_text(encoding="utf-8")
        html = (ROOT / "jobpilot" / "static" / "index.html").read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', init)
        self.assertIsNotNone(match)
        self.assertIn(f"V{match.group(1)}", html)


if __name__ == "__main__":
    unittest.main()
