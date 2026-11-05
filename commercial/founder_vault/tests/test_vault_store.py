import sys
import tempfile
import unittest
from pathlib import Path

COMMERCIAL_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COMMERCIAL_DIR))

from founder_vault.storage.vault_store import VaultStore


PASSWORD = "BBH-Founder-Secure-2026!"


class VaultStoreTests(unittest.TestCase):

    def test_add_and_restore_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "private.txt"
            source.write_bytes(b"Founder private document")

            store = VaultStore(root / "vault")
            doc_id = store.add_document(source, "other", PASSWORD)

            restored = root / "restored.txt"
            metadata = store.restore_document(
                doc_id, restored, PASSWORD
            )

            self.assertEqual(restored.read_bytes(), source.read_bytes())
            self.assertEqual(metadata["filename"], "private.txt")

    def test_wrong_password_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "document.txt"
            source.write_bytes(b"secret")

            store = VaultStore(root / "vault")
            doc_id = store.add_document(source, "pdf", PASSWORD)

            with self.assertRaises(Exception):
                store.restore_document(
                    doc_id, root / "output.txt", "Wrong-Password-2026!"
                )

    def test_invalid_category_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "document.txt"
            source.write_bytes(b"test")

            store = VaultStore(root / "vault")
            with self.assertRaises(ValueError):
                store.add_document(source, "unknown", PASSWORD)

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "document.txt"
            source.write_bytes(b"secret")

            store = VaultStore(root / "vault")
            doc_id = store.add_document(source, "other", PASSWORD)

            destination = root / "existing.txt"
            destination.write_bytes(b"keep this")

            with self.assertRaises(FileExistsError):
                store.restore_document(doc_id, destination, PASSWORD)

            self.assertEqual(destination.read_bytes(), b"keep this")

    def test_list_does_not_expose_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "my_nid_scan.pdf"
            source.write_bytes(b"private")

            store = VaultStore(root / "vault")
            store.add_document(source, "identity_document", PASSWORD)

            records = store.list_documents()
            self.assertEqual(len(records), 1)
            self.assertNotIn("filename", records[0])


if __name__ == "__main__":
    unittest.main()
