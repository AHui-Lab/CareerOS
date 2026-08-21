from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LauncherContractTests(unittest.TestCase):
    def test_launcher_derives_version_from_package(self):
        text = (ROOT / "start.ps1").read_text(encoding="utf-8")
        self.assertIn("jobpilot\\__init__.py", text)
        self.assertIn("Get-ExpectedVersion", text)
        self.assertNotIn('$ExpectedVersion = "0.3.0"', text)

    def test_launcher_can_recognize_stalled_jobpilot_process(self):
        text = (ROOT / "start.ps1").read_text(encoding="utf-8")
        self.assertIn("Test-LooksLikeJobPilotProcess", text)
        self.assertIn("Get-CimInstance Win32_Process", text)
        self.assertIn("stalled JobPilot", text)
        self.assertIn("will not terminate that process", text)

    def test_doctor_checks_both_services_and_resume_ready(self):
        text = (ROOT / "doctor.ps1").read_text(encoding="utf-8")
        self.assertIn("/api/health", text)
        self.assertIn("8765", text)
        self.assertIn("8766", text)
        self.assertIn("/api/jobpilot/experiences?resume_ready=true", text)
        self.assertIn("Resume Ready count", text)


if __name__ == "__main__":
    unittest.main()
