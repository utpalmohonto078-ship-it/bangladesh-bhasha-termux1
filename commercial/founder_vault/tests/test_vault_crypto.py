import sys
import tempfile
import unittest
from pathlib import Path

COMMERCIAL_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COMMERCIAL_DIR))

from founder_vault.security.vault_crypto import (
    encrypt_bytes,
    decrypt_bytes,
    encrypt_file,
    decrypt_file,
    VaultError,
    InvalidVaultFile,
)


PASSWORD = "BBH-Founder-Secure-2026!"


class VaultCryptoTests(unittest.TestCase):

    def test_encrypt_decrypt_bytes(self):
        original = b"BANGLADESH BHASHA VAULT TEST"
        encrypted = encrypt_bytes(original, PASSWORD)
        self.assertNotEqual(encrypted, original)
        self.assertEqual(decrypt_bytes(encrypted, PASSWORD), original)

    def test_wrong_password_rejected(self):
        encrypted = encrypt_bytes(b"private document", PASSWORD)
        with self.assertRaises(VaultError):
            decrypt_bytes(encrypted, "Wrong-Password-2026!")

    def test_tampered_data_rejected(self):
        encrypted = bytearray(encrypt_bytes(b"private data", PASSWORD))
        encrypted[-1] ^= 1
        with self.assertRaises(VaultError):
            decrypt_bytes(bytes(encrypted), PASSWORD)

    def test_invalid_format_rejected(self):
        with self.assertRaises(InvalidVaultFile):
            decrypt_bytes(b"invalid", PASSWORD)

    def test_file_encryption_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "document.txt"
            encrypted = root / "document.bbhv"
            restored = root / "restored.txt"

            original.write_bytes(b"Founder private file")

            encrypt_file(original, encrypted, PASSWORD)
            decrypt_file(encrypted, restored, PASSWORD)

            self.assertEqual(restored.read_bytes(), original.read_bytes())

            with self.assertRaises(FileExistsError):
                encrypt_file(original, encrypted, PASSWORD)

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            encrypt_bytes(b"test", "short")


if __name__ == "__main__":
    unittest.main()
