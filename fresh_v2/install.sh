#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=""

for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "Python 3.10+ ইনস্টল করুন।"
    exit 1
fi

if [ -f "$HERE/install.py" ]; then
    exec "$PYTHON" "$HERE/install.py"
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" -c 'import urllib.request; urllib.request.urlretrieve("https://raw.githubusercontent.com/utpalmohonto078-ship-it/bangladesh-bhasha/main/install.py", __import__("sys").argv[1])' "$TMP/install.py"
exec "$PYTHON" "$TMP/install.py"
