"""BBH Founder Vault encrypted sync API prototype."""

import hmac
import os
import uuid
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file


def create_app(sync_token, storage_dir, max_bytes=25 * 1024 * 1024):
    if not isinstance(sync_token, str) or len(sync_token) < 32:
        raise ValueError("SYNC_TOKEN must contain at least 32 characters.")

    root = Path(storage_dir).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)

    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = max_bytes
    app.config["SYNC_STORAGE"] = root
    app.config["MAX_SYNC_BYTES"] = max_bytes

    def authenticated():
        header = request.headers.get("Authorization", "")
        prefix = "Bearer "

        if not header.startswith(prefix):
            return False

        supplied = header[len(prefix):]
        return hmac.compare_digest(supplied, sync_token)

    def document_path(document_id):
        try:
            normalized = str(uuid.UUID(document_id))
        except (ValueError, TypeError, AttributeError):
            abort(400, description="Invalid document ID.")

        if normalized != document_id.lower():
            abort(400, description="Document ID must be a UUID.")

        return root / (normalized + ".bbhv")

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="File exceeds the upload limit."), 413

    @app.before_request
    def require_authentication():
        if not authenticated():
            return jsonify(error="Authentication required."), 401

    @app.post("/v1/sync/<document_id>")
    def upload(document_id):
        destination = document_path(document_id)

        if request.mimetype != "application/octet-stream":
            return jsonify(error="Use application/octet-stream."), 415

        payload = request.get_data(cache=False)

        if not payload:
            return jsonify(error="Empty payload rejected."), 400

        if len(payload) > app.config["MAX_SYNC_BYTES"]:
            return jsonify(error="Payload too large."), 413

        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        try:
            fd = os.open(str(destination), flags, 0o600)
        except FileExistsError:
            return jsonify(error="Document already exists; overwrite denied."), 409

        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        return jsonify(
            document_id=document_id,
            stored=True,
            encrypted_payload_bytes=len(payload),
        ), 201

    @app.get("/v1/sync/<document_id>")
    def download(document_id):
        source = document_path(document_id)

        if not source.is_file():
            return jsonify(error="Document not found."), 404

        return send_file(
            source,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=document_id + ".bbhv",
            conditional=False,
        )

    return app
