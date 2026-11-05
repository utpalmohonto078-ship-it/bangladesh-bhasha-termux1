"""Run the local BBH encrypted sync prototype."""

import os
from pathlib import Path

from founder_vault.sync.server_api import create_app


BASE = Path(__file__).resolve().parents[2]
TOKEN = os.environ.get("BBH_VAULT_SYNC_TOKEN", "")

if len(TOKEN) < 32:
    raise SystemExit(
        "Set BBH_VAULT_SYNC_TOKEN to a random secret of at least 32 characters."
    )

STORAGE = BASE / "data" / "vault_sync"

app = create_app(TOKEN, STORAGE)

if __name__ == "__main__":
    print("BBH Sync API: local development mode")
    print("Listening only on 127.0.0.1:8781")
    app.run(host="127.0.0.1", port=8781, debug=False)
