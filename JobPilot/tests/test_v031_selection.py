import unittest
from unittest.mock import AsyncMock, patch

from jobpilot.career_selection import filter_selected, rank_experiences
from jobpilot.main import ResumeGenerate, app, generate_resume


class CareerSelectionUnitTests(unittest.TestCase):
    def test_ranking_explains_matching_skills(self):
        experiences = [
            {
                "id": "rag-project",
                "category": "project",
                "title": "Local RAG system",
                "description": "Built retrieval pipeline and FastAPI service",
                "skills": ["Python", "FastAPI", "RAG"],
                "tags": ["Python", "FastAPI", "RAG"],
            },
            {
                "id": "music-project",
                "category": "project",
                "title": "Music analysis",
                "description": "Audio feature extraction",
                "skills": ["Music"],
                "tags": ["Audio"],
            },
        ]
        ranked = rank_experiences(experiences, "LLM 应用开发 Python FastAPI RAG Agent")
        self.assertEqual(ranked[0]["id"], "rag-project")
        self.assertGreater(ranked[0]["match_percent"], ranked[1]["match_percent"])
        self.assertTrue(any("技能/领域命中" in x or "JD 关键词命中" in x for x in ranked[0]["match_reasons"]))
        self.assertTrue(ranked[0]["selected_default"])

    def test_filter_selected_preserves_explicit_order(self):
        experiences = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        self.assertEqual([x["id"] for x in filter_selected(experiences, ["c", "a"])], ["c", "a"])

    def test_recommendation_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/careervault/recommendations", paths)


class HumanReviewedGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_generation_uses_only_human_selected_careervault_ids(self):
        cv_experiences = [
            {"id": "keep", "category": "project", "title": "Keep", "description": "Python"},
            {"id": "drop", "category": "project", "title": "Drop", "description": "Music"},
        ]
        generated = {"mode": "local", "sections": [], "skills": [], "autofill": {}}
        with (
            patch("jobpilot.main.db.get_profile", return_value={"email": "legacy@example.com"}),
            patch("jobpilot.main.db.list_experiences", return_value=[]),
            patch("jobpilot.main.careervault_all_resume_ready", new=AsyncMock(return_value={"profile": {"name": "CV User"}, "experiences": cv_experiences})),
            patch("jobpilot.main.careervault_context", new=AsyncMock()) as auto_context,
            patch("jobpilot.main.generate_tailored_resume", new=AsyncMock(return_value=generated)) as generator,
            patch("jobpilot.main.db.insert_resume_version", side_effect=lambda payload: {"id": 31, **payload}),
        ):
            result = await generate_resume(ResumeGenerate(
                target_role="AI Engineer",
                jd="Python FastAPI",
                careervault_experience_ids=["keep"],
            ))

        auto_context.assert_not_awaited()
        experiences_arg = generator.await_args.args[1]
        self.assertEqual([x["id"] for x in experiences_arg], ["keep"])
        self.assertEqual(result["selection_mode"], "careervault-human-reviewed")
        self.assertEqual(result["selected_careervault_ids"], ["keep"])
        self.assertEqual(result["item"]["resume"]["profile_snapshot"]["email"], "legacy@example.com")

    async def test_empty_reviewed_selection_is_rejected(self):
        with (
            patch("jobpilot.main.db.get_profile", return_value={}),
            patch("jobpilot.main.db.list_experiences", return_value=[]),
        ):
            with self.assertRaises(Exception) as ctx:
                await generate_resume(ResumeGenerate(target_role="Engineer", jd="Python", careervault_experience_ids=[]))
        self.assertIn("至少选择一条", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
