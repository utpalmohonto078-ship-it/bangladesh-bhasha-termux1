#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3 || command -v python || true)"
[ -n "$PYTHON" ] || { echo "Python পাওয়া যায়নি।"; exit 1; }

if [ -f "$HERE/uninstall.py" ]; then
    exec "$PYTHON" "$HERE/uninstall.py"
fi

if [ -n "${PREFIX:-}" ] && command -v pkg >/dev/null 2>&1; then
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}/bangladesh-bhasha"
else
    DATA="${XDG_DATA_HOME:-$HOME/.local/share}/bangladesh-bhasha"
fi

[ -f "$DATA/uninstall.py" ] || { echo "Uninstaller পাওয়া যায়নি: $DATA"; exit 1; }
exec "$PYTHON" "$DATA/uninstall.py"
