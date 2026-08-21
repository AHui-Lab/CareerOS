import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from careervault import store


class FileStoreTests(unittest.TestCase):
    def test_rejects_parent_traversal(self):
        with self.assertRaises(ValueError):
            store.safe_vault_path("../secret.txt")

    def test_text_file_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            vault = root / "vault"
            vault.mkdir()
            with patch.object(store, "VAULT", vault):
                store.write_text_file("inbox/note.md", "# hello\n")
                item = store.read_text_file("inbox/note.md")
                self.assertEqual(item["content"], "# hello\n")
                self.assertEqual(item["path"], "inbox/note.md")


if __name__ == "__main__":
    unittest.main()
