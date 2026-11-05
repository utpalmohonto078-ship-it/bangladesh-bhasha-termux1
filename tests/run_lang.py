import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "compiler"))
import lang

WANT = ["15", "ok", "loop", "loop", "300", "3"]
TEMPLATE = """{LET} a = 5
{LET} b = 10
{PRINT} a + b
{IF} a < b {AND} b < 20
    {PRINT} "ok"
{ELSE}
    {PRINT} "no"
{END}
{REPEAT} 2
    {PRINT} "loop"
{END}
{FUNCTION} add(x, y)
    {RETURN} x + y
{END}
{PRINT} add(100, 200)
{PRINT} {LEN}("abc")
"""
DIGITS = """সংখ্যা a = ২৫
সংখ্যা b = ۲۵
সংখ্যা c = ２５
দেখাও a + b + c
"""

def run(path):
    name = path.stem
    steps = [["compiler/ir.py", str(path)],
             ["compiler/ir_validate.py", f"build/{name}.ir.json"],
             ["compiler/bytecode.py", f"build/{name}.ir.json"],
             ["compiler/vm.py", f"build/{name}.bc.json"]]
    out = ""
    for args in steps:
        r = subprocess.run([sys.executable] + args, cwd=ROOT,
                           capture_output=True, text=True, timeout=60)
        out = (r.stdout + r.stderr).strip()
        if r.returncode != 0:
            return None, (out.splitlines() or ["error"])[-1]
    return [x for x in out.splitlines() if not x.startswith("PASS")], ""

def main():
    cases = [(c, TEMPLATE.format(**w), WANT) for c, w in lang.LANGS.items()]
    cases.append(("digits", DIGITS, ["75"]))
    bad = 0
    for code, text, want in cases:
        path = ROOT / "examples" / f"lang_{code}.bb"
        path.write_text(text, encoding="utf-8")
        got, err = run(path)
        ok = got == want
        bad += 0 if ok else 1
        print("PASS" if ok else "FAIL", code, "" if ok else (err or got))
    print(f"{len(cases) - bad}/{len(cases)} passed")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
