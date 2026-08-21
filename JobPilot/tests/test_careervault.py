import unittest

from jobpilot.careervault import normalize_experience, normalize_profile


class CareerVaultIntegrationTests(unittest.TestCase):
    def test_normalize_profile_uses_first_education(self):
        profile = normalize_profile({
            "name": "Test User",
            "city": "Tianjin",
            "headline": "AI application engineer",
            "github": "https://github.com/example",
            "education": [{
                "school": "Example University",
                "college": "Engineering",
                "major": "Electronic Information",
                "degree": "Master",
                "end": "2027-05",
                "gpa": "3.7",
            }],
        })
        self.assertEqual(profile["school"], "Example University")
        self.assertEqual(profile["current_city"], "Tianjin")
        self.assertEqual(profile["summary"], "AI application engineer")

    def test_normalize_experience_preserves_facts_and_results(self):
        item = normalize_experience({
            "id": "project-rag",
            "type": "project",
            "title": "RAG system",
            "organization": "Personal",
            "start": "2026-01",
            "facts": "- Built FastAPI backend\n- Added RAG pipeline",
            "results": "- 100 automated checks passed",
            "skills": ["Python", "FastAPI", "RAG"],
            "domains": ["AI"],
            "match_score": 0.8,
        })
        self.assertEqual(item["source"], "careervault:project-rag")
        self.assertIn("Built FastAPI backend", item["description"])
        self.assertIn("100 automated checks passed", item["highlights"])
        self.assertEqual(item["match_score"], 0.8)
        self.assertIn("FastAPI", item["tags"])


if __name__ == "__main__":
    unittest.main()

class CareerVaultResumeIdTests(unittest.IsolatedAsyncioTestCase):
    async def test_ai_generation_accepts_string_experience_ids(self):
        from unittest.mock import AsyncMock, patch
        from jobpilot.resume import generate_tailored_resume

        fake = {
            "headline": "AI Engineer",
            "summary": "summary",
            "selected_experience_ids": ["project-rag"],
            "selected_document_ids": [],
            "sections": [{"title": "项目经历", "items": []}],
            "skills": ["Python"],
        }
        experiences = [{
            "id": "project-rag",
            "category": "project",
            "title": "RAG System",
            "organization": "Personal",
            "description": "Built a RAG app",
            "highlights": ["Built a RAG app"],
            "tags": ["Python", "RAG"],
        }]
        with patch("jobpilot.resume.ai_enabled", return_value=True), patch("jobpilot.resume._chat_json", new=AsyncMock(return_value=fake)):
            result = await generate_tailored_resume({}, experiences, {"target_role": "AI Engineer", "target_jd": "RAG"}, [])
        self.assertEqual(result["mode"], "ai")
        self.assertEqual(result["selected_experience_ids"], ["project-rag"])
