import sys, json, dataclasses
sys.path.insert(0, ".")
sys.stdout.reconfigure(encoding="utf-8")
from compiler.lexer import tokenize
from compiler.parser import parse

def conv(n):
    if isinstance(n, list):
        return [conv(x) for x in n]
    if dataclasses.is_dataclass(n):
        d = {"t": type(n).__name__}
        for f in dataclasses.fields(n):
            d[f.name] = conv(getattr(n, f.name))
        return d
    if isinstance(n, float):
        s = repr(n)
        return {"float": s[:-2] if s.endswith(".0") else s}
    return n

src = open(sys.argv[1], encoding="utf-8").read()
try:
    out = conv(parse(tokenize(src)))
except SyntaxError as e:
    out = {"error": str(e)}
print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
