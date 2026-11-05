import json
import sys
from pathlib import Path

OPENERS = {"IF", "REPEAT", "FUNCTION"}

def validate(data):
    if data.get("format") != "BB-IR-1":
        raise ValueError("Unsupported IR format")

    instructions = data.get("instructions")
    if not isinstance(instructions, list):
        raise ValueError("Instructions must be a list")

    stack = []
    function_depth = 0

    for index, item in enumerate(instructions):
        if not isinstance(item, dict):
            raise ValueError(f"Instruction {index}: invalid structure")

        op = item.get("op")
        line = item.get("line", index + 1)

        if op in OPENERS:
            if op == "FUNCTION":
                function_depth += 1
            stack.append({"op": op, "line": line, "else_seen": False})

        elif op == "ELSE":
            if not stack or stack[-1]["op"] != "IF":
                raise ValueError(f"Line {line}: ELSE without IF")
            if stack[-1]["else_seen"]:
                raise ValueError(f"Line {line}: duplicate ELSE")
            stack[-1]["else_seen"] = True

        elif op == "END":
            if not stack:
                raise ValueError(f"Line {line}: END without block")
            closed = stack.pop()
            if closed["op"] == "FUNCTION":
                function_depth -= 1

        elif op == "RETURN":
            if function_depth == 0:
                raise ValueError(f"Line {line}: RETURN outside FUNCTION")

        elif op not in {"LET", "PRINT"}:
            raise ValueError(f"Line {line}: unknown operation {op}")

    if stack:
        block = stack[-1]
        raise ValueError(
            f"Unclosed {block['op']} block opened at line {block['line']}"
        )

    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python compiler/ir_validate.py build/advanced.ir.json")
        return 2

    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        validate(data)
        print("PASS: IR structure validated")
        print("PASS: All blocks are balanced")
        print("PASS: RETURN placement validated")
        return 0
    except Exception as error:
        print("IR VALIDATION ERROR:", error)
        return 1

if __name__ == "__main__":
    sys.exit(main())
