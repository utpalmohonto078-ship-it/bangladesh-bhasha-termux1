#!/usr/bin/env python3
import ast
import subprocess
import sys
from pathlib import Path

def check_file(filename):
    path = Path(filename)

    if not path.is_file():
        print(f"FAIL: File not found: {path}")
        return 1

    suffix = path.suffix.lower()

    try:
        if suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"))
            print(f"PASS: Python syntax: {path}")
            return 0

        if suffix in (".js", ".mjs", ".cjs"):
            result = subprocess.run(
                ["node", "--check", str(path)],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                print(f"PASS: JavaScript syntax: {path}")
                return 0
            print(result.stderr.strip())
            return 1

        print(f"SKIP: Unsupported file type: {suffix}")
        return 2

    except (SyntaxError, UnicodeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {path}: {exc}")
        return 1

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer/check.py file.py [file.js ...]")
        return 2

    results = [check_file(name) for name in sys.argv[1:]]
    return 1 if 1 in results else 0

if __name__ == "__main__":
    sys.exit(main())
