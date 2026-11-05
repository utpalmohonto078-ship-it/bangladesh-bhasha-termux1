#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/BANGLADESH-BHASHA-ULTIMATE"
V2="$ROOT/fresh_v2"
STAMP="$(date +%Y%m%d-%H%M%S)"

cd "$ROOT"
mkdir -p backups reports

# Preserve existing V2 before replacing its files
if [ -d "$V2" ]; then
  tar -czf "backups/fresh-v2-before-$STAMP.tar.gz" fresh_v2
fi

mkdir -p "$V2"/{compiler,runtime,tests,examples,docs}
touch "$V2/compiler/__init__.py" "$V2/runtime/__init__.py"

cat > "$V2/compiler/lexer.py" <<'PY'
import re
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int

PATTERN = re.compile(
    r'(?P<SPACE>[ \t]+)|(?P<NUMBER>\d+(?:\.\d+)?)|'
    r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|'
    r'(?P<IDENT>[^\W\d]\w*)|'
    r'(?P<OP>==|!=|<=|>=|[+\-*/%=<>(),])|'
    r'(?P<NEWLINE>\n)|(?P<COMMENT>\#.*)',
    re.UNICODE
)

KEYWORDS = {
    "সংখ্যা": "LET", "let": "LET", "var": "LET",
    "দেখাও": "PRINT", "print": "PRINT",
    "সত্য": "TRUE", "true": "TRUE",
    "মিথ্যা": "FALSE", "false": "FALSE",
}

def tokenize(source):
    tokens = []
    line = column = 1
    pos = 0
    while pos < len(source):
        match = PATTERN.match(source, pos)
        if not match:
            raise SyntaxError(
                f"Line {line}, column {column}: invalid character "
                f"{source[pos]!r}"
            )
        kind, value = match.lastgroup, match.group()
        if kind == "NEWLINE":
            tokens.append(Token("NEWLINE", value, line, column))
            line += 1
            column = 1
        else:
            if kind not in ("SPACE", "COMMENT"):
                if kind == "IDENT":
                    kind = KEYWORDS.get(value, "IDENT")
                tokens.append(Token(kind, value, line, column))
            column += len(value)
        pos = match.end()
    tokens.append(Token("EOF", "", line, column))
    return tokens
PY

cat > "$V2/compiler/ast_nodes.py" <<'PY'
from dataclasses import dataclass

@dataclass
class Program:
    statements: list

@dataclass
class Number:
    value: int | float

@dataclass
class String:
    value: str

@dataclass
class Boolean:
    value: bool

@dataclass
class Variable:
    name: str

@dataclass
class Binary:
    left: object
    operator: str
    right: object

@dataclass
class Unary:
    operator: str
    operand: object

@dataclass
class Declare:
    name: str
    value: object

@dataclass
class Print:
    value: object
PY

cat > "$V2/compiler/parser.py" <<'PY'
from . import ast_nodes as A

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def expect(self, kind):
        token = self.current()
        if token.kind != kind:
            raise SyntaxError(
                f"Line {token.line}: expected {kind}, got {token.value!r}"
            )
        return self.advance()

    def parse(self):
        statements = []
        while self.current().kind != "EOF":
            if self.current().kind == "NEWLINE":
                self.advance()
                continue
            statements.append(self.statement())
            if self.current().kind not in ("NEWLINE", "EOF"):
                t = self.current()
                raise SyntaxError(f"Line {t.line}: unexpected {t.value!r}")
        return A.Program(statements)

    def statement(self):
        if self.current().kind == "LET":
            self.advance()
            name = self.expect("IDENT").value
            self.expect("OP")
            if self.tokens[self.pos - 1].value != "=":
                raise SyntaxError("Expected '=' after variable name")
            return A.Declare(name, self.expression())
        if self.current().kind == "PRINT":
            self.advance()
            return A.Print(self.expression())
        t = self.current()
        raise SyntaxError(f"Line {t.line}: unknown statement {t.value!r}")

    def expression(self, minimum=0):
        left = self.prefix()
        precedence = {
            "==": 1, "!=": 1, "<": 1, ">": 1, "<=": 1, ">=": 1,
            "+": 2, "-": 2, "*": 3, "/": 3, "%": 3,
        }
        while self.current().kind == "OP":
            op = self.current().value
            level = precedence.get(op, -1)
            if level < minimum:
                break
            self.advance()
            right = self.expression(level + 1)
            left = A.Binary(left, op, right)
        return left

    def prefix(self):
        token = self.advance()
        if token.kind == "NUMBER":
            value = float(token.value) if "." in token.value else int(token.value)
            return A.Number(value)
        if token.kind == "STRING":
            import ast
            return A.String(ast.literal_eval(token.value))
        if token.kind == "TRUE":
            return A.Boolean(True)
        if token.kind == "FALSE":
            return A.Boolean(False)
        if token.kind == "IDENT":
            return A.Variable(token.value)
        if token.kind == "OP" and token.value in ("-", "+"):
            return A.Unary(token.value, self.expression(4))
        if token.kind == "OP" and token.value == "(":
            value = self.expression()
            self.expect("OP")
            if self.tokens[self.pos - 1].value != ")":
                raise SyntaxError("Expected ')'")
            return value
        raise SyntaxError(f"Line {token.line}: invalid expression {token.value!r}")

def parse(tokens):
    return Parser(tokens).parse()
PY

cat > "$V2/compiler/semantic.py" <<'PY'
from . import ast_nodes as A

def analyze(program):
    declared = set()

    def expression(node):
        if isinstance(node, A.Variable):
            if node.name not in declared:
                raise NameError(f"Undefined variable: {node.name}")
        elif isinstance(node, A.Binary):
            expression(node.left)
            expression(node.right)
        elif isinstance(node, A.Unary):
            expression(node.operand)
        elif not isinstance(node, (A.Number, A.String, A.Boolean)):
            raise TypeError(f"Unsupported expression: {type(node).__name__}")

    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            if stmt.name in declared:
                raise NameError(f"Duplicate variable: {stmt.name}")
            expression(stmt.value)
            declared.add(stmt.name)
        elif isinstance(stmt, A.Print):
            expression(stmt.value)
        else:
            raise TypeError(f"Unsupported statement: {type(stmt).__name__}")
    return True
PY

cat > "$V2/compiler/ir.py" <<'PY'
from . import ast_nodes as A

def generate(program):
    code = []

    def expression(node):
        if isinstance(node, A.Number):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.String):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Boolean):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Variable):
            code.append({"op": "LOAD", "name": node.name})
        elif isinstance(node, A.Unary):
            expression(node.operand)
            code.append({"op": "UNARY", "operator": node.operator})
        elif isinstance(node, A.Binary):
            expression(node.left)
            expression(node.right)
            code.append({"op": "BINARY", "operator": node.operator})

    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            expression(stmt.value)
            code.append({"op": "STORE", "name": stmt.name})
        elif isinstance(stmt, A.Print):
            expression(stmt.value)
            code.append({"op": "PRINT"})
    return {"format": "BB-V2-IR", "instructions": code}
PY

cat > "$V2/compiler/bytecode.py" <<'PY'
def compile_ir(ir):
    if ir.get("format") != "BB-V2-IR":
        raise ValueError("Invalid BB V2 IR format")
    allowed = {"CONST", "LOAD", "STORE", "PRINT", "BINARY", "UNARY"}
    code = []
    for index, item in enumerate(ir["instructions"]):
        if item.get("op") not in allowed:
            raise ValueError(f"Invalid IR instruction at {index}")
        code.append(dict(item))
    return {"format": "BB-V2-BC", "code": code}
PY

cat > "$V2/runtime/vm.py" <<'PY'
class VirtualMachine:
    def __init__(self):
        self.variables = {}
        self.output = []

    def run(self, program):
        if program.get("format") != "BB-V2-BC":
            raise ValueError("Invalid BB V2 bytecode")
        stack = []
        for pc, item in enumerate(program["code"]):
            op = item["op"]
            if op == "CONST":
                stack.append(item["value"])
            elif op == "LOAD":
                name = item["name"]
                if name not in self.variables:
                    raise RuntimeError(f"Undefined variable: {name}")
                stack.append(self.variables[name])
            elif op == "STORE":
                if not stack:
                    raise RuntimeError(f"Stack underflow at {pc}")
                self.variables[item["name"]] = stack.pop()
            elif op == "PRINT":
                if not stack:
                    raise RuntimeError(f"Stack underflow at {pc}")
                self.output.append(stack.pop())
            elif op == "UNARY":
                if not stack:
                    raise RuntimeError(f"Stack underflow at {pc}")
                value = stack.pop()
                stack.append(-value if item["operator"] == "-" else +value)
            elif op == "BINARY":
                if len(stack) < 2:
                    raise RuntimeError(f"Stack underflow at {pc}")
                right, left = stack.pop(), stack.pop()
                op = item["operator"]
                operations = {
                    "+": lambda: left + right,
                    "-": lambda: left - right,
                    "*": lambda: left * right,
                    "/": lambda: left / right,
                    "%": lambda: left % right,
                    "==": lambda: left == right,
                    "!=": lambda: left != right,
                    "<": lambda: left < right,
                    ">": lambda: left > right,
                    "<=": lambda: left <= right,
                    ">=": lambda: left >= right,
                }
                if op not in operations:
                    raise RuntimeError(f"Unsupported operator: {op}")
                stack.append(operations[op]())
        if stack:
            raise RuntimeError("VM finished with a non-empty stack")
        return self.output
PY

cat > "$V2/bb.py" <<'PY'
import sys
from pathlib import Path
from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.semantic import analyze
from compiler.ir import generate
from compiler.bytecode import compile_ir
from runtime.vm import VirtualMachine

def compile_source(source):
    tokens = tokenize(source)
    ast = parse(tokens)
    analyze(ast)
    ir = generate(ast)
    return compile_ir(ir)

def run_source(source):
    return VirtualMachine().run(compile_source(source))

def main():
    if len(sys.argv) != 2:
        print("Usage: python bb.py FILE.bb")
        raise SystemExit(2)
    path = Path(sys.argv[1])
    result = run_source(path.read_text(encoding="utf-8"))
    for item in result:
        print(item)

if __name__ == "__main__":
    main()
PY

cat > "$V2/examples/hello.bb" <<'EOF'
সংখ্যা x = 10
সংখ্যা y = x * 2 + 5
দেখাও y
দেখাও "BANGLADESH BHASHA V2"
EOF

cat > "$V2/tests/test_v2.py" <<'PY'
import unittest
from bb import compile_source, run_source

class FreshV2Tests(unittest.TestCase):
    def test_bengali(self):
        self.assertEqual(run_source(
            "সংখ্যা x = 10\nদেখাও x + 5\n"
        ), [15])

    def test_english(self):
        self.assertEqual(run_source(
            "let x = 8\nprint x * 3\n"
        ), [24])

    def test_precedence(self):
        self.assertEqual(run_source(
            "দেখাও 2 + 3 * 4\n"
        ), [14])

    def test_boolean(self):
        self.assertEqual(run_source(
            "দেখাও সত্য == সত্য\n"
        ), [True])

    def test_undefined_variable(self):
        with self.assertRaises(NameError):
            compile_source("দেখাও unknown\n")

    def test_duplicate_variable(self):
        with self.assertRaises(NameError):
            compile_source("সংখ্যা x = 1\nসংখ্যা x = 2\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
PY

cat > "$V2/docs/STATUS.md" <<'EOF'
# Fresh V2 status

Implemented in this first foundation:
- Lexer
- AST nodes
- Pratt expression parser
- Semantic variable checks
- IR generation
- Bytecode validation
- Stack-based VM
- Bengali and English basic syntax
- Automated initial tests

Not yet implemented:
- Functions, scopes and GLOBAL
- Branches and loops
- Collections
- Exceptions
- OOP
- Modules and package manager
- Standard library
- Debugger, REPL, sandbox and native compilation

This is a tested foundation, not a production release.
EOF

echo "[1/4] Python syntax check"
python -m py_compile \
  "$V2"/compiler/*.py "$V2"/runtime/*.py \
  "$V2"/bb.py "$V2"/tests/*.py

echo "[2/4] Fresh V2 tests"
cd "$V2"
PYTHONPATH="$V2" python -m unittest discover -s tests -v

echo "[3/4] Example execution"
python bb.py examples/hello.bb

echo "[4/4] Build report"
cd "$ROOT"
{
  echo "BANGLADESH BHASHA ULTIMATE FRESH V2"
  date
  find fresh_v2 -type f | sort
  echo
  echo "Latest V1 commit:"
  git log -1 --oneline
} > "reports/fresh-v2-$STAMP.txt"

echo
echo "FRESH V2 FOUNDATION BUILD SUCCESS"
echo "Project: $V2"
echo "Report: reports/fresh-v2-$STAMP.txt"
echo "Backup: $BACKUP"
