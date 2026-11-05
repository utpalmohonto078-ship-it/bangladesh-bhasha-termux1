"""Encrypted document storage for BBH Founder Vault."""

import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from founder_vault.security.vault_crypto import encrypt_bytes, decrypt_bytes


CATEGORIES = {
    "photo",
    "identity_document",
    "certificate",
    "pdf",
    "other",
}


class VaultStore:
    def __init__(self, vault_dir):
        self.root = Path(vault_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

        self.db_path = self.root / "vault.sqlite3"
        self.init_db()

    def connect(self):
        db = sqlite3.connect(self.db_path)
        db.row_factory = sqlite3.Row
        os.chmod(self.db_path, 0o600)
        return db

    def init_db(self):
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    encrypted_payload BLOB NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def add_document(self, source, category, password):
        source = Path(source).expanduser()

        if not source.is_file():
            raise FileNotFoundError(source)

        if category not in CATEGORIES:
            raise ValueError("Unsupported document category.")

        content = source.read_bytes()

        metadata = {
            "filename": source.name,
            "category": category,
            "sha256": hashlib.sha256(content).hexdigest(),
            "size": len(content),
        }

        package = json.dumps({
            "metadata": metadata,
            "content": content.hex(),
        }).encode("utf-8")

        encrypted = encrypt_bytes(package, password)
        document_id = uuid.uuid4().hex
        created_at = datetime.now(timezone.utc).isoformat()

        with self.connect() as db:
            db.execute(
                """INSERT INTO documents
                   (document_id, encrypted_payload, created_at)
                   VALUES (?, ?, ?)""",
                (document_id, encrypted, created_at),
            )

        return document_id

    def list_documents(self):
        with self.connect() as db:
            rows = db.execute("""
                SELECT document_id, created_at
                FROM documents
                ORDER BY created_at DESC
            """).fetchall()

        return [dict(row) for row in rows]

    def restore_document(self, document_id, destination, password):
        destination = Path(destination).expanduser()

        if destination.exists():
            raise FileExistsError(destination)

        with self.connect() as db:
            row = db.execute(
                "SELECT encrypted_payload FROM documents WHERE document_id=?",
                (document_id,),
            ).fetchone()

        if row is None:
            raise KeyError("Document not found.")

        package = decrypt_bytes(bytes(row["encrypted_payload"]), password)
        data = json.loads(package.decode("utf-8"))

        content = bytes.fromhex(data["content"])
        metadata = data["metadata"]

        digest = hashlib.sha256(content).hexdigest()
        if digest != metadata["sha256"]:
            raise ValueError("Document integrity check failed.")

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(str(destination), flags, 0o600)

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return metadata
