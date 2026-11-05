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

def check(path):
    name = path.stem
    want = expectation(path)
    if want is None:
        return False, "no '# expect:' line"
    steps = [
        ["compiler/ir.py", str(path)],
        ["compiler/ir_validate.py", f"build/{name}.ir.json"],
        ["compiler/bytecode.py", f"build/{name}.ir.json"],
        ["compiler/vm.py", f"build/{name}.bc.json"],
    ]
    for args in steps:
        try:
            code, out = stage(args)
        except subprocess.TimeoutExpired:
            return False, "timeout"
        if code != 0:
            last = out.splitlines()[-1] if out else ""
            if want in out:
                return True, last
            return False, f"wanted '{want}' but got: {last}"
    return False, "was ACCEPTED (should be rejected)"

def main():
    files = sorted((ROOT / "tests" / "negative").glob("*.bb"))
    bad = 0
    for f in files:
        ok, msg = check(f)
        print(("PASS" if ok else "FAIL"), f.stem, "->", msg)
        bad += 0 if ok else 1
    print(f"{len(files) - bad}/{len(files)} passed")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
