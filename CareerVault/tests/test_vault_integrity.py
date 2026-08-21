import unittest

from careervault.store import EXPERIENCES, experience_to_dict


class VaultIntegrityTests(unittest.TestCase):
    def test_all_experience_files_parse_and_match_folder_id(self):
        seen = set()
        for path in EXPERIENCES.glob('*/index.md'):
            item = experience_to_dict(path)
            self.assertEqual(item.get('id'), path.parent.name, path)
            self.assertNotIn(item.get('id'), seen, path)
            seen.add(item.get('id'))
            self.assertIsInstance(item.get('resume_ready'), bool, path)
            self.assertIn(item.get('status'), {'idea', 'draft', 'active', 'verified', 'archived'}, path)
            self.assertIsInstance(item.get('domains'), list, path)
            self.assertIsInstance(item.get('skills'), list, path)
            self.assertTrue(str(item.get('title') or '').strip(), path)

    def test_migration_drafts_cannot_leak_to_jobpilot(self):
        for path in EXPERIENCES.glob('*/index.md'):
            item = experience_to_dict(path)
            if item.get('migration_review') == 'required':
                self.assertFalse(item.get('resume_ready'), path)


if __name__ == '__main__':
    unittest.main()
