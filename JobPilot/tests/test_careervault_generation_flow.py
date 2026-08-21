import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from jobpilot.main import ResumeGenerate, generate_resume


class CareerVaultGenerationFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_generation_uses_careervault_and_ignores_legacy_bank(self):
        local_profile = {"name": "Legacy Name", "email": "legacy@example.com", "school": "Legacy U"}
        local_experiences = [{"id": 1, "title": "Legacy Project", "category": "project"}]
        cv_experience = {
            "id": "project-rag",
            "category": "project",
            "title": "RAG System",
            "organization": "Personal",
            "description": "Built a RAG system",
            "highlights": ["Built a RAG system"],
            "tags": ["Python", "RAG"],
        }
        cv = {
            "source": "careervault",
            "profile": {"name": "CareerVault Name", "school": "CareerVault U", "email": ""},
            "experiences": [cv_experience],
        }
        generated = {
            "mode": "local",
            "headline": "AI Engineer",
            "sections": [],
            "skills": ["Python"],
            "autofill": {"name": "CareerVault Name"},
        }

        with (
            patch("jobpilot.main.db.get_profile", return_value=local_profile),
            patch("jobpilot.main.db.list_experiences", return_value=local_experiences),
            patch("jobpilot.main.careervault_context", new=AsyncMock(return_value=cv)) as cv_context,
            patch("jobpilot.main.generate_tailored_resume", new=AsyncMock(return_value=generated)) as generator,
            patch("jobpilot.main.db.insert_resume_version", side_effect=lambda payload: {"id": 9, **payload}) as insert_version,
        ):
            result = await generate_resume(ResumeGenerate(target_role="AI Engineer", jd="Python RAG FastAPI"))

        self.assertEqual(result["source"], "careervault")
        cv_context.assert_awaited_once()
        generator.assert_awaited_once()
        profile_arg, experiences_arg, target_arg, docs_arg = generator.await_args.args
        self.assertEqual(profile_arg["name"], "CareerVault Name")
        self.assertEqual(profile_arg["school"], "CareerVault U")
        # Blank CareerVault values must not erase useful local recovery fields.
        self.assertEqual(profile_arg["email"], "legacy@example.com")
        self.assertEqual(experiences_arg, [cv_experience])
        self.assertNotIn(local_experiences[0], experiences_arg)
        self.assertEqual(target_arg["target_role"], "AI Engineer")
        self.assertIsNone(docs_arg)

        saved = insert_version.call_args.args[0]
        self.assertEqual(saved["resume"]["source"], "careervault")
        self.assertEqual(saved["resume"]["profile_snapshot"]["name"], "CareerVault Name")

    async def test_connected_careervault_without_resume_ready_facts_is_a_hard_stop(self):
        cv = {"source": "careervault", "profile": {"name": "User"}, "experiences": []}
        with (
            patch("jobpilot.main.db.get_profile", return_value={}),
            patch("jobpilot.main.db.list_experiences", return_value=[{"id": 1, "title": "Legacy"}]),
            patch("jobpilot.main.careervault_context", new=AsyncMock(return_value=cv)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await generate_resume(ResumeGenerate(target_role="Engineer", jd="Python"))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Resume Ready", ctx.exception.detail)

    async def test_offline_careervault_does_not_silently_use_legacy_facts(self):
        with (
            patch("jobpilot.main.db.get_profile", return_value={}),
            patch("jobpilot.main.db.list_experiences", return_value=[{"id": 1, "title": "Legacy"}]),
            patch("jobpilot.main.careervault_context", new=AsyncMock(return_value=None)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await generate_resume(ResumeGenerate(target_role="Engineer", jd="Python"))

        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("CareerVault 未连接", ctx.exception.detail)

    async def test_explicit_legacy_ids_are_only_offline_escape_hatch(self):
        local_profile = {"name": "Legacy"}
        local_experiences = [
            {"id": 1, "title": "Keep", "category": "project"},
            {"id": 2, "title": "Ignore", "category": "project"},
        ]
        generated = {"mode": "local", "sections": [], "skills": [], "autofill": {}}

        with (
            patch("jobpilot.main.db.get_profile", return_value=local_profile),
            patch("jobpilot.main.db.list_experiences", return_value=local_experiences),
            patch("jobpilot.main.careervault_context", new=AsyncMock()) as cv_context,
            patch("jobpilot.main.generate_tailored_resume", new=AsyncMock(return_value=generated)) as generator,
            patch("jobpilot.main.db.insert_resume_version", side_effect=lambda payload: {"id": 10, **payload}),
        ):
            result = await generate_resume(ResumeGenerate(target_role="Engineer", jd="Python", experience_ids=[1]))

        cv_context.assert_not_awaited()
        experiences_arg = generator.await_args.args[1]
        self.assertEqual([x["id"] for x in experiences_arg], [1])
        self.assertEqual(result["source"], "jobpilot-local-legacy")


if __name__ == "__main__":
    unittest.main()
