import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from license_engine import issue_license, verify_license, revoke_license


class LicenseEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "test.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def test_issue_and_verify(self):
        result = issue_license(
            "customer@example.com", "Professional", 30, self.db
        )
        checked = verify_license(result["key"], self.db)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["plan"], "Professional")

    def test_unknown_key(self):
        checked = verify_license("not-a-real-license", self.db)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["reason"], "invalid_key")

    def test_revoke(self):
        result = issue_license(
            "customer@example.com", "Enterprise", 30, self.db
        )
        self.assertTrue(revoke_license(result["key"], self.db))
        checked = verify_license(result["key"], self.db)
        self.assertFalse(checked["valid"])
        self.assertEqual(checked["reason"], "revoked")

    def test_invalid_plan(self):
        with self.assertRaises(ValueError):
            issue_license("customer@example.com", "Unknown", 30, self.db)

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            issue_license("customer@example.com", "Professional", 0, self.db)


if __name__ == "__main__":
    unittest.main()
