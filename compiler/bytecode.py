import ast
from bnexpr import parse_expr
import bcext
import json
import re
import sys
from pathlib import Path

BINARY = {
    ast.Add: "ADD", ast.Sub: "SUB",
    ast.Mult: "MUL", ast.Div: "DIV",
    ast.FloorDiv: "FLOORDIV", ast.Mod: "MOD",
    ast.Pow: "POW",
}
COMPARE = {
    ast.Eq: "EQ", ast.NotEq: "NE",
    ast.Gt: "GT", ast.GtE: "GTE",
    ast.Lt: "LT", ast.LtE: "LTE",
}
UNARY = {ast.UAdd: "POS", ast.USub: "NEG"}

def expression(node, code, line, functions):
    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float, str, bool, type(None)):
            raise ValueError(f"Line {line}: unsupported constant")
        code.append({"op": "PUSH", "value": node.value, "line": line})

    elif isinstance(node, ast.Name):
        code.append({"op": "LOAD", "name": node.id, "line": line})

    elif isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        expression(node.left, code, line, functions)
        expression(node.right, code, line, functions)
        code.append({"op": BINARY[type(node.op)], "line": line})

    elif isinstance(node, ast.UnaryOp) and type(node.op) in UNARY:
        expression(node.operand, code, line, functions)
        code.append({"op": UNARY[type(node.op)], "line": line})

    elif isinstance(node, ast.Compare) and len(node.ops) == 1:
        expression(node.left, code, line, functions)
        expression(node.comparators[0], code, line, functions)
        op = COMPARE.get(type(node.ops[0]))
        if not op:
            raise ValueError(f"Line {line}: unsupported comparison")
        code.append({"op": op, "line": line})

    elif bcext.handles(node, functions):
        bcext.emit(node, code, line, functions, expression)

    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        name = node.func.id
        if name not in functions:
            raise ValueError(f"Line {line}: unknown function {name}")
        if node.keywords:
            raise ValueError(f"Line {line}: keyword arguments unsupported")
        info = functions[name]
        params = info["params"] if isinstance(info, dict) else info
        if len(node.args) != len(params):
            raise ValueError(f"Line {line}: wrong argument count for {name}")
        for arg in node.args:
            expression(arg, code, line, functions)
        code.append({
            "op": "CALL", "name": name,
            "argc": len(node.args), "line": line
        })

    elif isinstance(node, ast.BoolOp):
        is_and = isinstance(node.op, ast.And)
        end_jumps = []
        false_jumps = []
        for value in node.values:
            expression(value, code, line, functions)
            idx = len(code)
            code.append({"op": "JUMP_IF_FALSE", "target": None, "line": line})
            if is_and:
                false_jumps.append(idx)
            else:
                code.append({"op": "PUSH", "value": True, "line": line})
                end_jumps.append(len(code))
                code.append({"op": "JUMP", "target": None, "line": line})
                code[idx]["target"] = len(code)
        if is_and:
            code.append({"op": "PUSH", "value": True, "line": line})
            end_jumps.append(len(code))
            code.append({"op": "JUMP", "target": None, "line": line})
            for i in false_jumps:
                code[i]["target"] = len(code)
            code.append({"op": "PUSH", "value": False, "line": line})
        else:
            code.append({"op": "PUSH", "value": False, "line": line})
        for i in end_jumps:
            code[i]["target"] = len(code)

    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        expression(node.operand, code, line, functions)
        j = len(code)
        code.append({"op": "JUMP_IF_FALSE", "target": None, "line": line})
        code.append({"op": "PUSH", "value": False, "line": line})
        e = len(code)
        code.append({"op": "JUMP", "target": None, "line": line})
        code[j]["target"] = len(code)
        code.append({"op": "PUSH", "value": True, "line": line})
        code[e]["target"] = len(code)

    else:
        raise ValueError(f"Line {line}: unsupported expression")

def compile_ir(data):
    if data.get("format") != "BB-IR-1":
        raise ValueError("Unsupported IR format")

    source = data.get("instructions")
    if not isinstance(source, list):
        raise ValueError("Invalid IR instructions")

    functions = {}
    for item in source:
        if item.get("op") == "FUNCTION":
            match = re.fullmatch(
                r"(?:FUNCTION|ফাংশন)\s+([A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*)\s*\((.*?)\)",
                item.get("source", "")
            )
            if not match:
                raise ValueError(
                    f"Line {item.get('line')}: invalid function declaration"
                )
            name, raw_params = match.groups()
            params = [p.strip() for p in raw_params.split(",") if p.strip()]
            if len(set(params)) != len(params):
                raise ValueError(f"Duplicate parameter in {name}")
            if any(not re.fullmatch(r"[A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*", p) for p in params):
                raise ValueError(f"Invalid parameter in {name}")
            if name in functions:
                raise ValueError(f"Duplicate function: {name}")
            functions[name] = params

    code = []
    blocks = []
    defined = set()

    for item in source:
        op = item["op"]
        line = item.get("line", 0)

        if op == "LET":
            expression(parse_expr(item["value"], mode="eval").body,
                       code, line, functions)
            code.append({"op": "STORE", "name": item["name"], "line": line})

        elif op == "PRINT":
            expression(parse_expr(item["value"], mode="eval").body,
                       code, line, functions)
            code.append({"op": "PRINT", "line": line})

        elif op == "IF":
            expression(parse_expr(item["condition"], mode="eval").body,
                       code, line, functions)
            jump = len(code)
            code.append({"op": "JUMP_IF_FALSE", "target": None, "line": line})
            blocks.append({"type": "IF", "jump": jump, "else": None})

        elif op == "ELSE":
            if not blocks or blocks[-1]["type"] != "IF":
                raise ValueError(f"Line {line}: invalid ELSE")
            block = blocks[-1]
            if block["else"] is not None:
                raise ValueError(f"Line {line}: duplicate ELSE")
            jump = len(code)
            code.append({"op": "JUMP", "target": None, "line": line})
            block["else"] = jump
            code[block["jump"]]["target"] = len(code)

        elif op == "REPEAT":
            expression(parse_expr(item["count"], mode="eval").body,
                       code, line, functions)
            code.append({"op": "REPEAT_INIT", "line": line})
            start = len(code)
            jump = len(code)
            code.append({"op": "REPEAT_CHECK", "target": None, "line": line})
            blocks.append({
                "type": "REPEAT", "start": start, "jump": jump
            })

        elif op == "FUNCTION":
            if blocks:
                raise ValueError(f"Line {line}: nested function is unsupported")
            name = re.fullmatch(
                r"(?:FUNCTION|ফাংশন)\s+([A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*)\s*\(.*\)",
                item["source"]
            ).group(1)
            skip = len(code)
            code.append({"op": "JUMP", "target": None, "line": line})
            functions[name] = {
                "params": functions[name],
                "target": len(code)
            }
            defined.add(name)
            blocks.append({"type": "FUNCTION", "skip": skip})

        elif op == "RETURN":
            if not any(b["type"] == "FUNCTION" for b in blocks):
                raise ValueError(f"Line {line}: RETURN outside FUNCTION")
            expression(parse_expr(item["value"], mode="eval").body,
                       code, line, functions)
            code.append({"op": "RETURN", "line": line})

        elif op == "END":
            if not blocks:
                raise ValueError(f"Line {line}: unmatched END")
            block = blocks.pop()

            if block["type"] == "IF":
                target = len(code)
                if block["else"] is None:
                    code[block["jump"]]["target"] = target
                else:
                    code[block["else"]]["target"] = target

            elif block["type"] == "REPEAT":
                code.append({
                    "op": "REPEAT_NEXT",
                    "target": block["start"], "line": line
                })
                code[block["jump"]]["target"] = len(code)

            elif block["type"] == "FUNCTION":
                code.append({"op": "PUSH", "value": None, "line": line})
                code.append({"op": "RETURN", "line": line})
                code[block["skip"]]["target"] = len(code)

        else:
            raise ValueError(f"Line {line}: unsupported operation {op}")

    if blocks:
        raise ValueError("Unclosed block")

    for name, info in functions.items():
        if isinstance(info, dict) and name not in defined:
            raise ValueError(f"Function not compiled: {name}")

    return {
        "format": "BB-BC-1",
        "functions": functions,
        "instructions": code
    }

def main():
    if len(sys.argv) != 2:
        print("Usage: python compiler/bytecode.py build/file.ir.json")
        return 2
    try:
        source = Path(sys.argv[1])
        data = json.loads(source.read_text(encoding="utf-8"))
        result = compile_ir(data)
        output = Path("build") / (source.name.replace(".ir.json", ".bc.json"))
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("PASS: Bytecode generated:", output)
        print("Instructions:", len(result["instructions"]))
        print("Functions:", sum(
            isinstance(v, dict) for v in result["functions"].values()
        ))
        return 0
    except Exception as exc:
        print("BYTECODE ERROR:", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
