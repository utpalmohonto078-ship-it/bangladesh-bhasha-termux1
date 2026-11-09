import sys, json
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from compiler.lexer import tokenize
src = open(sys.argv[1], encoding="utf-8").read()
try:
    out = [[t.kind, t.value, t.line, t.column] for t in tokenize(src)]
except SyntaxError as e:
    out = {"error": str(e)}
print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
