from pathlib import Path
import unittest

from jobpilot.autofill import build_flat_package, build_structured_autofill

ROOT = Path(__file__).resolve().parents[1]


class StructuredAutofillTests(unittest.TestCase):
    def test_builds_education_internship_and_project_arrays(self):
        version = {
            "id": 7,
            "name": "Example · AI Engineer",
            "target_company": "Example",
            "target_role": "AI Engineer",
            "resume": {
                "profile_snapshot": {
                    "name": "User",
                    "school": "Example University",
                    "major": "Computer Science",
                    "degree": "Bachelor",
                    "graduation_date": "2027-06",
                },
                "summary": "AI application engineer",
                "skills": ["Python", "FastAPI"],
                "sections": [
                    {"title": "实习经历", "items": [{"source_id": "intern-1", "organization": "ACME", "title": "Software Intern", "date": "2025-07 - 2025-09", "location": "Shanghai", "bullets": ["Built API"]}]},
                    {"title": "项目经历", "items": [{"source_id": "project-1", "organization": "Personal", "title": "RAG", "date": "2026-01 - 2026-03", "location": "", "bullets": ["Built RAG pipeline"]}]},
                ],
            },
            "autofill": {},
        }
        structured = build_structured_autofill(version, {})
        self.assertEqual(structured["schema_version"], 2)
        self.assertEqual(structured["education"][0]["school"], "Example University")
        self.assertEqual(structured["internships"][0]["organization"], "ACME")
        self.assertEqual(structured["internships"][0]["start_date"], "2025-07")
        self.assertEqual(structured["internships"][0]["end_date"], "2025-09")
        self.assertEqual(structured["projects"][0]["title"], "RAG")
        self.assertIn("Python", structured["skills"])

        flat = build_flat_package(version, {})
        self.assertIn("ACME", flat["internship_experience"])
        self.assertIn("RAG", flat["project_experience"])
        self.assertEqual(flat["name"], "User")


class AtsAdapterContractTests(unittest.TestCase):
    def test_runtime_contains_supported_adapters_and_never_submit_contract(self):
        text = (ROOT / "extension" / "autofill-runtime.js").read_text(encoding="utf-8")
        for marker in ("italent\\.cn", "beisen\\.com", "mokahr\\.com", "nowcoder\\.com", "北森 / iTalent", "Moka", "牛客"):
            self.assertIn(marker, text)
        self.assertIn("forbiddenButton", text)
        self.assertIn("保存并提交", text)
        self.assertIn("下一步", text)
        self.assertIn("JobPilot 未点击任何提交/下一步按钮", text)

    def test_popup_uses_structured_runtime(self):
        popup = (ROOT / "extension" / "popup.js").read_text(encoding="utf-8")
        self.assertIn("data.structured", popup)
        self.assertIn("autofill-runtime.js", popup)
        self.assertIn("window.JobPilotAutofill.run", popup)


if __name__ == "__main__":
    unittest.main()
