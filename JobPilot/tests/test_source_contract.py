import unittest

from jobpilot.main import ResumeGenerate, app


class CareerVaultOnlyContractTests(unittest.TestCase):
    def test_obsidian_api_routes_are_removed(self):
        paths = {route.path for route in app.routes}
        self.assertNotIn('/api/vault/documents', paths)
        self.assertNotIn('/api/vault/import', paths)

    def test_resume_generate_payload_has_no_vault_toggle(self):
        fields = set(ResumeGenerate.model_fields)
        self.assertNotIn('use_vault', fields)
        self.assertIn('experience_ids', fields)

    def test_health_exposes_careervault_first_contract(self):
        # Static route presence is enough here; network availability is environment-specific.
        paths = {route.path for route in app.routes}
        self.assertIn('/api/health', paths)
        self.assertIn('/api/resume/generate', paths)


if __name__ == '__main__':
    unittest.main()
