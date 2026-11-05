#!/usr/bin/env python3
"""BANGLADESH BHASHA — Advanced Language Engine"""

import ast
import operator
import re
import sys
from pathlib import Path

VERSION = "ULTIMATE-1.0"
MAX_DEPTH = 30
MAX_LOOP = 10000

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}

COMPARE = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

class UtpalError(Exception):
    pass

class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class Runtime:
    def __init__(self):
        self.variables = {}
        self.functions = {}

    def evaluate(self, expression, env=None, depth=0):
        if depth > MAX_DEPTH:
            raise UtpalError("Function depth limit exceeded")
        try:
            tree = ast.parse(expression, mode="eval")
            return self.safe_node(tree.body, env or self.variables, depth)
        except (SyntaxError, ZeroDivisionError, TypeError, ValueError) as exc:
            raise UtpalError(str(exc)) from exc

    def safe_node(self, node, env, depth):
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float, str, bool):
                return node.value
            raise UtpalError("Unsupported value")

        if isinstance(node, ast.Name):
            if node.id not in env:
                raise UtpalError(f"Unknown variable: {node.id}")
            return env[node.id]

        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left = self.safe_node(node.left, env, depth)
            right = self.safe_node(node.right, env, depth)

            if isinstance(node.op, ast.Mult):
                if isinstance(left, str) or isinstance(right, str):
                    if len(str(left)) * len(str(right)) > 10000:
                        raise UtpalError("String size limit exceeded")

            result = OPS[type(node.op)](left, right)

            if isinstance(result, int) and result.bit_length() > 10000:
                raise UtpalError("Integer size limit exceeded")
            if isinstance(result, float) and abs(result) > 1e100:
                raise UtpalError("Number limit exceeded")
            return result

        if isinstance(node, ast.UnaryOp):
            value = self.safe_node(node.operand, env, depth)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            if isinstance(node.op, ast.Not):
                return not value

        if isinstance(node, ast.Compare):
            left = self.safe_node(node.left, env, depth)
            for op, comparator in zip(node.ops, node.comparators):
                right = self.safe_node(comparator, env, depth)
                if type(op) not in COMPARE:
                    raise UtpalError("Unsupported comparison")
                if not COMPARE[type(op)](left, right):
                    return False
                left = right
            return True

        if isinstance(node, ast.BoolOp):
            values = [self.safe_node(v, env, depth) for v in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in self.functions:
                raise UtpalError(f"Unknown function: {name}")
            if node.keywords:
                raise UtpalError("Keyword arguments are not supported")
            args = [self.safe_node(a, env, depth) for a in node.args]
            return self.call_function(name, args, env, depth + 1)

        raise UtpalError("Unsafe or unsupported expression")

    def call_function(self, name, args, parent_env, depth):
        if depth > MAX_DEPTH:
            raise UtpalError("Function depth limit exceeded")

        params, body = self.functions[name]
        if len(args) != len(params):
            raise UtpalError(f"{name}: expected {len(params)} arguments")

        local = dict(parent_env)
        local.update(zip(params, args))

        try:
            self.execute(body, local, depth)
        except ReturnSignal as signal:
            return signal.value
        return None

    @staticmethod
    def block_end(lines, start):
        nesting = 0
        else_index = None

        for i in range(start + 1, len(lines)):
            word = lines[i].strip().split(maxsplit=1)[0:1]
            command = word[0] if word else ""

            if command in ("IF", "যদি", "REPEAT", "পুনরাবৃত্তি",
                           "FUNCTION", "ফাংশন"):
                nesting += 1
            elif command in ("END", "শেষ"):
                if nesting == 0:
                    return else_index, i
                nesting -= 1
            elif command in ("ELSE", "নাহলে") and nesting == 0:
                else_index = i

        raise UtpalError("Missing END / শেষ")

    def execute(self, lines, env=None, depth=0):
        if depth > MAX_DEPTH:
            raise UtpalError("Execution depth limit exceeded")

        env = self.variables if env is None else env
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line or line.startswith("#"):
                continue

            if line in ("END", "শেষ", "ELSE", "নাহলে"):
                raise UtpalError(f"Unexpected block command: {line}")

            if line.startswith(("IF ", "যদি ")):
                condition = line.split(maxsplit=1)[1]
                else_i, end_i = self.block_end(lines, i - 1)
                boundary = else_i if else_i is not None else end_i
                body = lines[i:boundary]
                alternative = (
                    lines[else_i + 1:end_i]
                    if else_i is not None else []
                )
                if self.evaluate(condition, env, depth):
                    self.execute(body, env, depth + 1)
                elif alternative:
                    self.execute(alternative, env, depth + 1)
                i = end_i + 1
                continue

            if line.startswith(("REPEAT ", "পুনরাবৃত্তি ")):
                count = self.evaluate(line.split(maxsplit=1)[1], env, depth)
                if type(count) is not int or not 0 <= count <= MAX_LOOP:
                    raise UtpalError("Loop count must be 0 to 10000")
                _, end_i = self.block_end(lines, i - 1)
                body = lines[i:end_i]
                for _ in range(count):
                    self.execute(body, env, depth + 1)
                i = end_i + 1
                continue

            if line.startswith(("FUNCTION ", "ফাংশন ")):
                match = re.fullmatch(
                    r"(?:FUNCTION|ফাংশন)\s+([A-Za-z_]\w*)\s*"
                    r"\(([A-Za-z_,\s]*)\)",
                    line
                )
                if not match:
                    raise UtpalError("Invalid FUNCTION syntax")
                name, raw_params = match.groups()
                params = [p.strip() for p in raw_params.split(",") if p.strip()]
                if len(params) != len(set(params)):
                    raise UtpalError("Duplicate function parameter")
                if not all(re.fullmatch(r"[A-Za-z_]\w*", p) for p in params):
                    raise UtpalError("Invalid function parameter")
                _, end_i = self.block_end(lines, i - 1)
                self.functions[name] = (params, lines[i:end_i])
                i = end_i + 1
                continue

            if line.startswith(("LET ", "সংখ্যা ")):
                match = re.fullmatch(
                    r"(?:LET|সংখ্যা)\s+([A-Za-z_]\w*)\s*=\s*(.+)",
                    line
                )
                if not match:
                    raise UtpalError("Invalid variable syntax")
                name, expression = match.groups()
                env[name] = self.evaluate(expression, env, depth)
                continue

            if line.startswith(("PRINT ", "দেখাও ")):
                expression = re.sub(r"^(PRINT|দেখাও)\s+", "", line)
                print(self.evaluate(expression, env, depth))
                continue

            if line.startswith(("RETURN ", "ফেরত ")):
                expression = re.sub(r"^(RETURN|ফেরত)\s+", "", line)
                raise ReturnSignal(self.evaluate(expression, env, depth))

            if line in ("HELP", "সাহায্য"):
                print("LET / সংখ্যা name = expression")
                print("PRINT / দেখাও expression")
                print("IF / যদি condition ... ELSE / নাহলে ... END / শেষ")
                print("REPEAT / পুনরাবৃত্তি count ... END / শেষ")
                print("FUNCTION / ফাংশন name(args) ... RETURN / ফেরত value ... END")
                continue

            if line in ("EXIT", "বন্ধ"):
                return

            raise UtpalError(f"Unknown command: {line}")

    def run_file(self, filename):
        path = Path(filename)
        if path.suffix != ".bb":
            raise UtpalError("File extension must be .bb")
        if not path.is_file():
            raise UtpalError("Source file not found")
        source = path.read_text(encoding="utf-8")
        if len(source) > 100_000:
            raise UtpalError("Source file too large")

        for number, line in enumerate(source.splitlines(), 1):
            pass

        try:
            self.execute(source.splitlines())
            return 0
        except ReturnSignal:
            raise UtpalError("RETURN used outside a function")
        except Exception as exc:
            print(f"[BHASHA ERROR] {exc}")
            return 1

def main():
    print(f"BANGLADESH BHASHA ULTIMATE {VERSION}")
    if len(sys.argv) != 2:
        print("Usage: python core/bb.py examples/advanced.bb")
        return 2
    try:
        return Runtime().run_file(sys.argv[1])
    except Exception as exc:
        print(f"[BHASHA ERROR] {exc}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
