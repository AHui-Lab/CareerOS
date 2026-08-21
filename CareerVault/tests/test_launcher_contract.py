from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LauncherContractTests(unittest.TestCase):
    def test_run_py_does_not_open_browser(self):
        text = (ROOT / "run.py").read_text(encoding="utf-8")
        self.assertNotIn("webbrowser", text)
        self.assertNotIn("threading.Timer", text)

    def test_windows_launcher_owns_browser_open(self):
        text = (ROOT / "start.ps1").read_text(encoding="utf-8")
        self.assertIn("Start-Process $BaseUrl", text)


if __name__ == "__main__":
    unittest.main()
