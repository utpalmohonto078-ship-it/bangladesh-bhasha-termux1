import sys
import tempfile
import unittest
import uuid
from pathlib import Path

COMMERCIAL_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(COMMERCIAL_DIR))

from founder_vault.sync.server_api import create_app


TOKEN = "test-only-secret-token-with-more-than-32-chars"


class SyncServerTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(
            TOKEN,
            Path(self.tmp.name) / "server",
            max_bytes=1024,
        )
        self.client = self.app.test_client()
        self.headers = {
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/octet-stream",
        }
        self.doc_id = str(uuid.uuid4())

    def tearDown(self):
        self.tmp.cleanup()

    def test_upload_and_download(self):
        payload = b"BBH encrypted payload only"

        response = self.client.post(
            f"/v1/sync/{self.doc_id}",
            data=payload,
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 201)

        downloaded = self.client.get(
            f"/v1/sync/{self.doc_id}",
            headers=self.headers,
        )
        self.assertEqual(downloaded.status_code, 200)
        self.assertEqual(downloaded.data, payload)

    def test_authentication_required(self):
        response = self.client.get(f"/v1/sync/{self.doc_id}")
        self.assertEqual(response.status_code, 401)

    def test_wrong_token_rejected(self):
        response = self.client.get(
            f"/v1/sync/{self.doc_id}",
            headers={"Authorization": "Bearer wrong-token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_upload_rejected(self):
        url = f"/v1/sync/{self.doc_id}"

        first = self.client.post(
            url, data=b"first", headers=self.headers
        )
        second = self.client.post(
            url, data=b"second", headers=self.headers
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 409)

    def test_invalid_document_id_rejected(self):
        response = self.client.get(
            "/v1/sync/not-a-uuid",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_payload_rejected(self):
        response = self.client.post(
            f"/v1/sync/{self.doc_id}",
            data=b"",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 400)

    def test_wrong_content_type_rejected(self):
        response = self.client.post(
            f"/v1/sync/{self.doc_id}",
            data=b"payload",
            headers={
                "Authorization": "Bearer " + TOKEN,
                "Content-Type": "text/plain",
            },
        )
        self.assertEqual(response.status_code, 415)

    def test_upload_size_limit(self):
        response = self.client.post(
            f"/v1/sync/{self.doc_id}",
            data=b"x" * 2048,
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 413)

    def test_invalid_short_server_secret(self):
        with self.assertRaises(ValueError):
            create_app("short", Path(self.tmp.name) / "bad")


if __name__ == "__main__":
    unittest.main()
