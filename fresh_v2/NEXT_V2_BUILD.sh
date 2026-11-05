#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

V2="$PWD"
ROOT="$(dirname "$V2")"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$ROOT/backups" "$ROOT/reports"
tar -czf "$ROOT/backups/v2-control-flow-$STAMP.tar.gz" \
  --exclude='__pycache__' .

echo "[1/7] Updating AST..."

cat > compiler/ast_nodes.py <<'PY'
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
class Call:
    name: str
    args: list

@dataclass
class Declare:
    name: str
    value: object

@dataclass
class Assign:
    name: str
    value: object

@dataclass
class Print:
    value: object

@dataclass
class If:
    condition: object
    body: list
    otherwise: list

@dataclass
class Repeat:
    count: object
    body: list

@dataclass
class Function:
    name: str
    params: list
    body: list

@dataclass
class Return:
    value: object

@dataclass
class Global:
    name: str
PY

echo "[2/7] Updating Unicode lexer..."

cat > compiler/lexer.py <<'PY'
import re
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int

PATTERN = re.compile(
    r'(?P<SPACE>[ \t]+)|'
    r'(?P<NUMBER>\d+(?:\.\d+)?)|'
    r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|'
    r'(?P<IDENT>[^\W\d][\w\u0980-\u09FF]*)|'
    r'(?P<OP>==|!=|<=|>=|[+\-*/%=<>(),])|'
    r'(?P<NEWLINE>\n)|'
    r'(?P<COMMENT>\#.*)',
    re.UNICODE
)

KEYWORDS = {
    "সংখ্যা": "LET", "let": "LET", "var": "LET",
    "দেখাও": "PRINT", "print": "PRINT",
    "সত্য": "TRUE", "true": "TRUE",
    "মিথ্যা": "FALSE", "false": "FALSE",
    "যদি": "IF", "if": "IF",
    "নাহলে": "ELSE", "else": "ELSE",
    "শেষ": "END", "end": "END",
    "পুনরাবৃত্তি": "REPEAT", "repeat": "REPEAT",
    "ফাংশন": "FUNCTION", "function": "FUNCTION",
    "ফেরত": "RETURN", "return": "RETURN",
    "গ্লোবাল": "GLOBAL", "global": "GLOBAL",
}

def tokenize(source):
    tokens = []
    line = column = 1
    pos = 0

    while pos < len(source):
        match = PATTERN.match(source, pos)
        if not match:
            raise SyntaxError(
                f"Line {line}, column {column}: "
                f"invalid character {source[pos]!r}"
            )

        kind = match.lastgroup
        value = match.group()

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

echo "[3/7] Updating parser..."

cat > compiler/parser.py <<'PY'
from . import ast_nodes as A
import ast as py_ast

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.current()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def expect(self, kind):
        token = self.current()
        if token.kind != kind:
            raise SyntaxError(
                f"Line {token.line}: expected {kind}, got {token.value!r}"
            )
        return self.advance()

    def expect_op(self, value):
        token = self.expect("OP")
        if token.value != value:
            raise SyntaxError(
                f"Line {token.line}: expected {value!r}"
            )

    def newlines(self):
        while self.current().kind == "NEWLINE":
            self.advance()

    def line_end(self):
        if self.current().kind not in ("NEWLINE", "EOF"):
            t = self.current()
            raise SyntaxError(f"Line {t.line}: unexpected {t.value!r}")
        self.newlines()

    def block(self, stops):
        statements = []
        self.newlines()

        while self.current().kind not in stops:
            if self.current().kind == "EOF":
                raise SyntaxError("Unexpected EOF: block is not closed")
            statements.append(self.statement())
            self.line_end()

        return statements

    def parse(self):
        statements = self.block({"EOF"})
        return A.Program(statements)

    def statement(self):
        kind = self.current().kind

        if kind == "LET":
            self.advance()
            name = self.expect("IDENT").value
            self.expect_op("=")
            return A.Declare(name, self.expression())

        if kind == "PRINT":
            self.advance()
            return A.Print(self.expression())

        if kind == "GLOBAL":
            self.advance()
            return A.Global(self.expect("IDENT").value)

        if kind == "RETURN":
            self.advance()
            return A.Return(self.expression())

        if kind == "IF":
            self.advance()
            condition = self.expression()
            self.line_end()
            body = self.block({"ELSE", "END"})
            otherwise = []

            if self.current().kind == "ELSE":
                self.advance()
                self.line_end()
                otherwise = self.block({"END"})

            self.expect("END")
            return A.If(condition, body, otherwise)

        if kind == "REPEAT":
            self.advance()
            count = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Repeat(count, body)

        if kind == "FUNCTION":
            self.advance()
            name = self.expect("IDENT").value
            self.expect_op("(")
            params = []

            if not (self.current().kind == "OP"
                    and self.current().value == ")"):
                params.append(self.expect("IDENT").value)
                while (self.current().kind == "OP"
                       and self.current().value == ","):
                    self.advance()
                    params.append(self.expect("IDENT").value)

            self.expect_op(")")
            if len(params) != len(set(params)):
                raise SyntaxError(f"Duplicate parameter in {name}")

            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Function(name, params, body)

        if kind == "IDENT":
            name = self.advance().value
            self.expect_op("=")
            return A.Assign(name, self.expression())

        t = self.current()
        raise SyntaxError(
            f"Line {t.line}: unknown statement {t.value!r}"
        )

    def expression(self, minimum=0):
        left = self.prefix()

        precedence = {
            "==": 1, "!=": 1, "<": 1, ">": 1,
            "<=": 1, ">=": 1,
            "+": 2, "-": 2,
            "*": 3, "/": 3, "%": 3,
        }

        while True:
            if (self.current().kind == "OP"
                    and self.current().value == "("):
                if not isinstance(left, A.Variable):
                    break
                self.advance()
                args = []

                if not (self.current().kind == "OP"
                        and self.current().value == ")"):
                    args.append(self.expression())
                    while (self.current().kind == "OP"
                           and self.current().value == ","):
                        self.advance()
                        args.append(self.expression())

                self.expect_op(")")
                left = A.Call(left.name, args)
                continue

            if self.current().kind != "OP":
                break

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
            return A.String(py_ast.literal_eval(token.value))

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
            self.expect_op(")")
            return value

        raise SyntaxError(
            f"Line {token.line}: invalid expression {token.value!r}"
        )

def parse(tokens):
    return Parser(tokens).parse()
PY

echo "[4/7] Updating semantic analyzer..."

cat > compiler/semantic.py <<'PY'
from . import ast_nodes as A

def analyze(program):
    top_globals = set()
    functions = {}

    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            if stmt.name in top_globals:
                raise NameError(f"Duplicate variable: {stmt.name}")
            top_globals.add(stmt.name)

        elif isinstance(stmt, A.Function):
            if stmt.name in functions:
                raise NameError(f"Duplicate function: {stmt.name}")
            functions[stmt.name] = stmt

    def collect_globals(body, result):
        for stmt in body:
            if isinstance(stmt, A.Global):
                result.add(stmt.name)
            elif isinstance(stmt, A.If):
                collect_globals(stmt.body, result)
                collect_globals(stmt.otherwise, result)
            elif isinstance(stmt, A.Repeat):
                collect_globals(stmt.body, result)

    def collect_locals(body, result):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                result.add(stmt.name)
            elif isinstance(stmt, A.If):
                collect_locals(stmt.body, result)
                collect_locals(stmt.otherwise, result)
            elif isinstance(stmt, A.Repeat):
                collect_locals(stmt.body, result)

    def expression(node, scope, in_function):
        if isinstance(node, A.Variable):
            if node.name not in scope and node.name not in top_globals:
                raise NameError(f"Undefined variable: {node.name}")

        elif isinstance(node, A.Call):
            if node.name not in functions:
                raise NameError(f"Unknown function: {node.name}")
            expected = len(functions[node.name].params)
            if len(node.args) != expected:
                raise TypeError(
                    f"{node.name}: expected {expected} arguments, "
                    f"got {len(node.args)}"
                )
            for arg in node.args:
                expression(arg, scope, in_function)

        elif isinstance(node, A.Binary):
            expression(node.left, scope, in_function)
            expression(node.right, scope, in_function)

        elif isinstance(node, A.Unary):
            expression(node.operand, scope, in_function)

        elif not isinstance(node, (A.Number, A.String, A.Boolean)):
            raise TypeError(f"Unsupported expression: {type(node).__name__}")

    def statements(body, scope, in_function, declared_globals):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                if stmt.name in scope:
                    raise NameError(f"Duplicate local variable: {stmt.name}")
                if stmt.name in declared_globals:
                    raise NameError(f"{stmt.name} is declared GLOBAL")
                expression(stmt.value, scope, in_function)
                scope.add(stmt.name)

            elif isinstance(stmt, A.Assign):
                if stmt.name not in scope and stmt.name not in declared_globals:
                    raise NameError(f"Assignment to undeclared variable: {stmt.name}")
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.Print):
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.If):
                expression(stmt.condition, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)
                statements(stmt.otherwise, scope, in_function, declared_globals)

            elif isinstance(stmt, A.Repeat):
                expression(stmt.count, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)

            elif isinstance(stmt, A.Return):
                if not in_function:
                    raise SyntaxError("RETURN outside function")
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.Global):
                if not in_function:
                    raise SyntaxError("GLOBAL outside function")
                if stmt.name not in top_globals:
                    raise NameError(f"Unknown global variable: {stmt.name}")

    for stmt in program.statements:
        if isinstance(stmt, A.Function):
            globals_set = set()
            collect_globals(stmt.body, globals_set)

            if globals_set.intersection(stmt.params):
                raise SyntaxError("GLOBAL cannot conflict with a parameter")

            locals_set = set(stmt.params)
            collect_locals(stmt.body, locals_set)

            if globals_set.intersection(locals_set):
                raise SyntaxError("GLOBAL cannot conflict with a local variable")

            scope = set(stmt.params) | locals_set
            statements(stmt.body, scope, True, globals_set)

        elif not isinstance(stmt, A.Declare):
            statements([stmt], set(), False, set())

    # Validate initializers after collecting all top-level declarations.
    scope = set()
    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            expression(stmt.value, scope, False)
            scope.add(stmt.name)

    return True
PY

echo "[5/7] Updating IR, bytecode and VM..."

cat > compiler/ir.py <<'PY'
from . import ast_nodes as A

def generate(program):
    code = []
    functions = {}

    def expr(node):
        if isinstance(node, A.Number):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.String):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Boolean):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Variable):
            code.append({"op": "LOAD", "name": node.name})
        elif isinstance(node, A.Unary):
            expr(node.operand)
            code.append({"op": "UNARY", "operator": node.operator})
        elif isinstance(node, A.Binary):
            expr(node.left)
            expr(node.right)
            code.append({"op": "BINARY", "operator": node.operator})
        elif isinstance(node, A.Call):
            for arg in node.args:
                expr(arg)
            code.append({
                "op": "CALL", "name": node.name, "argc": len(node.args)
            })

    def globals_in(body):
        found = set()
        for stmt in body:
            if isinstance(stmt, A.Global):
                found.add(stmt.name)
            elif isinstance(stmt, A.If):
                found |= globals_in(stmt.body)
                found |= globals_in(stmt.otherwise)
            elif isinstance(stmt, A.Repeat):
                found |= globals_in(stmt.body)
        return sorted(found)

    def block(body):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                expr(stmt.value)
                code.append({"op": "STORE", "name": stmt.name})

            elif isinstance(stmt, A.Assign):
                expr(stmt.value)
                code.append({"op": "STORE", "name": stmt.name})

            elif isinstance(stmt, A.Print):
                expr(stmt.value)
                code.append({"op": "PRINT"})

            elif isinstance(stmt, A.Return):
                expr(stmt.value)
                code.append({"op": "RETURN"})

            elif isinstance(stmt, A.Global):
                pass

            elif isinstance(stmt, A.If):
                expr(stmt.condition)
                jf = len(code)
                code.append({"op": "JUMP_IF_FALSE", "target": -1})
                block(stmt.body)

                if stmt.otherwise:
                    jmp = len(code)
                    code.append({"op": "JUMP", "target": -1})
                    code[jf]["target"] = len(code)
                    block(stmt.otherwise)
                    code[jmp]["target"] = len(code)
                else:
                    code[jf]["target"] = len(code)

            elif isinstance(stmt, A.Repeat):
                expr(stmt.count)
                begin = len(code)
                code.append({"op": "LOOP_BEGIN", "target": -1})
                block(stmt.body)
                code.append({"op": "LOOP_NEXT", "target": begin + 1})
                code[begin]["target"] = len(code)

    # Functions are placed before the main program.
    # A jump prevents normal execution from entering function bodies.
    jump_main = len(code)
    code.append({"op": "JUMP", "target": -1})

    for stmt in program.statements:
        if isinstance(stmt, A.Function):
            functions[stmt.name] = {
                "params": stmt.params,
                "globals": globals_in(stmt.body),
                "target": len(code),
            }
            block(stmt.body)
            code.append({"op": "CONST", "value": None})
            code.append({"op": "RETURN"})

    code[jump_main]["target"] = len(code)

    main = [s for s in program.statements if not isinstance(s, A.Function)]
    block(main)

    return {
        "format": "BB-V2-IR",
        "instructions": code,
        "functions": functions,
    }
PY

cat > compiler/bytecode.py <<'PY'
def compile_ir(ir):
    if ir.get("format") != "BB-V2-IR":
        raise ValueError("Invalid BB V2 IR format")

    allowed = {
        "CONST", "LOAD", "STORE", "PRINT", "BINARY", "UNARY",
        "CALL", "RETURN", "JUMP", "JUMP_IF_FALSE",
        "LOOP_BEGIN", "LOOP_NEXT",
    }

    code = ir.get("instructions")
    if not isinstance(code, list):
        raise ValueError("IR instructions must be a list")

    for index, item in enumerate(code):
        if not isinstance(item, dict) or item.get("op") not in allowed:
            raise ValueError(f"Invalid IR instruction at {index}")

        if item["op"] in ("JUMP", "JUMP_IF_FALSE", "LOOP_BEGIN", "LOOP_NEXT"):
            target = item.get("target")
            if not isinstance(target, int) or not 0 <= target <= len(code):
                raise ValueError(f"Invalid jump target at {index}")

    functions = ir.get("functions", {})
    for name, info in functions.items():
        if not isinstance(info, dict):
            raise ValueError(f"Invalid function metadata: {name}")
        target = info.get("target")
        params = info.get("params")
        if not isinstance(target, int) or not 0 <= target < len(code):
            raise ValueError(f"Invalid function target: {name}")
        if not isinstance(params, list):
            raise ValueError(f"Invalid function parameters: {name}")

    return {
        "format": "BB-V2-BC",
        "code": [dict(item) for item in code],
        "functions": functions,
    }
PY

cat > runtime/vm.py <<'PY'
class VirtualMachine:
    def __init__(self):
        self.variables = {}
        self.output = []
        self.stack = []
        self.frames = []

    def pop(self):
        if not self.stack:
            raise RuntimeError("Stack underflow")
        return self.stack.pop()

    def run(self, program):
        if program.get("format") != "BB-V2-BC":
            raise ValueError("Invalid BB V2 bytecode")

        code = program["code"]
        functions = program.get("functions", {})
        ip = 0
        steps = 0
        max_steps = 1_000_000

        while ip < len(code):
            steps += 1
            if steps > max_steps:
                raise RuntimeError("Execution step limit exceeded")

            item = code[ip]
            op = item["op"]
            next_ip = ip + 1

            if op == "CONST":
                self.stack.append(item["value"])

            elif op == "LOAD":
                name = item["name"]
                if self.frames and name in self.frames[-1]["globals"]:
                    if name not in self.variables:
                        raise RuntimeError(f"Undefined global: {name}")
                    self.stack.append(self.variables[name])
                elif self.frames and name in self.frames[-1]["locals"]:
                    self.stack.append(self.frames[-1]["locals"][name])
                elif name in self.variables:
                    self.stack.append(self.variables[name])
                else:
                    raise RuntimeError(f"Undefined variable: {name}")

            elif op == "STORE":
                value = self.pop()
                name = item["name"]
                if self.frames and name in self.frames[-1]["globals"]:
                    self.variables[name] = value
                elif self.frames:
                    self.frames[-1]["locals"][name] = value
                else:
                    self.variables[name] = value

            elif op == "PRINT":
                self.output.append(self.pop())

            elif op == "UNARY":
                value = self.pop()
                if item["operator"] == "-":
                    self.stack.append(-value)
                else:
                    self.stack.append(+value)

            elif op == "BINARY":
                right = self.pop()
                left = self.pop()
                operator = item["operator"]

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

                if operator not in operations:
                    raise RuntimeError(f"Unsupported operator: {operator}")
                self.stack.append(operations[operator]())

            elif op == "JUMP":
                next_ip = item["target"]

            elif op == "JUMP_IF_FALSE":
                if not self.pop():
                    next_ip = item["target"]

            elif op == "LOOP_BEGIN":
                count = self.pop()
                if isinstance(count, bool) or not isinstance(count, (int, float)):
                    raise RuntimeError("REPEAT count must be numeric")
                if int(count) != count or count < 0:
                    raise RuntimeError("REPEAT count must be a non-negative integer")

                if count == 0:
                    next_ip = item["target"]
                else:
                    loops = self.frames[-1]["loops"] if self.frames else self.main_loops
                    loops.append({"remaining": int(count), "start": ip + 1})

            elif op == "LOOP_NEXT":
                loops = self.frames[-1]["loops"] if self.frames else self.main_loops
                if not loops:
                    raise RuntimeError("LOOP_NEXT without LOOP_BEGIN")
                loops[-1]["remaining"] -= 1
                if loops[-1]["remaining"] > 0:
                    next_ip = item["target"]
                else:
                    loops.pop()

            elif op == "CALL":
                name = item["name"]
                if name not in functions:
                    raise RuntimeError(f"Unknown function: {name}")

                info = functions[name]
                argc = item["argc"]
                params = info["params"]

                if argc != len(params):
                    raise RuntimeError(f"{name}: argument mismatch")

                args = [self.pop() for _ in range(argc)][::-1]

                if len(self.frames) >= 100:
                    raise RuntimeError("Call depth exceeded")

                self.frames.append({
                    "return_ip": next_ip,
                    "locals": dict(zip(params, args)),
                    "globals": set(info.get("globals", [])),
                    "loops": [],
                })
                next_ip = info["target"]

            elif op == "RETURN":
                result = self.pop()
                if not self.frames:
                    raise RuntimeError("RETURN without CALL")

                frame = self.frames.pop()
                self.stack.append(result)
                next_ip = frame["return_ip"]

            else:
                raise RuntimeError(f"Unknown opcode: {op}")

            ip = next_ip

        if self.frames:
            raise RuntimeError("Unfinished function call")
        if self.stack:
            raise RuntimeError("VM finished with a non-empty stack")

        return self.output

    @property
    def main_loops(self):
        if not hasattr(self, "_main_loops"):
            self._main_loops = []
        return self._main_loops
PY

echo "[6/7] Updating compiler entry..."

cat > bb.py <<'PY'
import sys
from pathlib import Path
from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.semantic import analyze
from compiler.ir import generate
from compiler.bytecode import compile_ir
from runtime.vm import VirtualMachine

def compile_source(source):
    ast = parse(tokenize(source))
    analyze(ast)
    return compile_ir(generate(ast))

def run_source(source):
    return VirtualMachine().run(compile_source(source))

def main():
    if len(sys.argv) != 2:
        print("Usage: python bb.py FILE.bb")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    for result in run_source(path.read_text(encoding="utf-8")):
        print(result)

if __name__ == "__main__":
    main()
PY

echo "[7/7] Installing expanded tests..."

cat > tests/test_v2.py <<'PY'
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
        self.assertEqual(run_source("দেখাও 2 + 3 * 4\n"), [14])

    def test_boolean(self):
        self.assertEqual(run_source("দেখাও সত্য == সত্য\n"), [True])

    def test_undefined_variable(self):
        with self.assertRaises(NameError):
            compile_source("দেখাও unknown\n")

    def test_duplicate_variable(self):
        with self.assertRaises(NameError):
            compile_source("সংখ্যা x = 1\nসংখ্যা x = 2\n")

    def test_if_else(self):
        src = (
            "সংখ্যা x = 8\n"
            "যদি x > 5\n"
            "দেখাও 1\n"
            "নাহলে\n"
            "দেখাও 0\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [1])

    def test_repeat(self):
        src = (
            "পুনরাবৃত্তি 3\n"
            "দেখাও 7\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [7, 7, 7])

    def test_nested_repeat(self):
        src = (
            "পুনরাবৃত্তি 2\n"
            "পুনরাবৃত্তি 2\n"
            "দেখাও 1\n"
            "শেষ\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [1, 1, 1, 1])

    def test_function(self):
        src = (
            "ফাংশন যোগ(a, b)\n"
            "ফেরত a + b\n"
            "শেষ\n"
            "দেখাও যোগ(10, 5)\n"
        )
        self.assertEqual(run_source(src), [15])

    def test_recursion(self):
        src = (
            "ফাংশন fact(n)\n"
            "যদি n <= 1\n"
            "ফেরত 1\n"
            "শেষ\n"
            "ফেরত n * fact(n - 1)\n"
            "শেষ\n"
            "দেখাও fact(5)\n"
        )
        self.assertEqual(run_source(src), [120])

    def test_global_write(self):
        src = (
            "সংখ্যা total = 10\n"
            "ফাংশন change()\n"
            "গ্লোবাল total\n"
            "total = total + 5\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
            "দেখাও total\n"
        )
        self.assertEqual(run_source(src), [15, 15])

    def test_global_inside_nested_block(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "যদি সত্য\n"
            "গ্লোবাল total\n"
            "শেষ\n"
            "total = total * 3\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
        )
        self.assertEqual(run_source(src), [6])

    def test_global_outside_function(self):
        with self.assertRaises(SyntaxError):
            compile_source("গ্লোবাল x\n")

    def test_global_parameter_conflict(self):
        src = (
            "সংখ্যা x = 1\n"
            "ফাংশন f(x)\n"
            "গ্লোবাল x\n"
            "ফেরত x\n"
            "শেষ\n"
        )
        with self.assertRaises(SyntaxError):
            compile_source(src)

    def test_function_argument_count(self):
        src = (
            "ফাংশন f(a)\n"
            "ফেরত a\n"
            "শেষ\n"
            "দেখাও f()\n"
        )
        with self.assertRaises(TypeError):
            compile_source(src)

    def test_return_outside_function(self):
        with self.assertRaises(SyntaxError):
            compile_source("ফেরত 5\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
PY

python -m py_compile compiler/*.py runtime/*.py bb.py tests/*.py
PYTHONPATH="$V2" python -m unittest discover -s tests -v

echo
echo "V2 CONTROL FLOW BUILD FINISHED"
echo "Backup: $ROOT/backups/v2-control-flow-$STAMP.tar.gz"
