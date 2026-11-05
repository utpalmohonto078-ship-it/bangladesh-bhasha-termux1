import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def stage(args):
    r = subprocess.run(
        [sys.executable] + args, cwd=ROOT,
        capture_output=True, text=True, timeout=60
    )
    return r.returncode, (r.stdout + r.stderr).strip()

def expectation(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    first = lines[0] if lines else ""
    if first.startswith("# expect:"):
        return first[len("# expect:"):].strip()
    return None
