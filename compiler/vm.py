import json
from vmext import EXT_OPS, run_ext
import operator
import sys
from pathlib import Path

BINARY = {
    "ADD": operator.add, "SUB": operator.sub,
    "MUL": operator.mul, "DIV": operator.truediv,
    "FLOORDIV": operator.floordiv, "MOD": operator.mod,
    "POW": operator.pow,
}
COMPARE = {
    "EQ": operator.eq, "NE": operator.ne,
    "GT": operator.gt, "GTE": operator.ge,
    "LT": operator.lt, "LTE": operator.le,
}

def safe_value(value, line):
    if type(value) in (int, float) and abs(value) > 10**100:
        raise RuntimeError(f"Line {line}: numeric limit exceeded")
    if isinstance(value, str) and len(value) > 100000:
        raise RuntimeError(f"Line {line}: string limit exceeded")
    return value

def run(program):
    if program.get("format") != "BB-BC-1":
        raise RuntimeError("Unsupported bytecode format")

    code = program["instructions"]
    functions = program["functions"]
    if len(code) > 10000:
        raise RuntimeError("Instruction limit exceeded")

    stack = []
    globals_ = {}
    frames = []
    loops = [{}]
    ip = 0
    steps = 0

    while ip < len(code):
        steps += 1
        if steps > 1000000:
            raise RuntimeError("Execution step limit exceeded")

        item = code[ip]
        op = item["op"]
        line = item.get("line", "?")
        next_ip = ip + 1

        def pop():
            if not stack:
                raise RuntimeError(f"Line {line}: stack underflow")
            return stack.pop()

        if op == "PUSH":
            stack.append(safe_value(item["value"], line))

        elif op == "LOAD":
            name = item["name"]
            if frames and name in frames[-1]["locals"]:
                stack.append(frames[-1]["locals"][name])
            elif name in globals_:
                stack.append(globals_[name])
            else:
                raise RuntimeError(f"Line {line}: undefined variable {name}")

        elif op == "STORE":
            value = pop()
            if frames:
                frames[-1]["locals"][item["name"]] = value
            else:
                globals_[item["name"]] = value

        elif op == "PRINT":
            print(pop())

        elif op in BINARY:
            right, left = pop(), pop()
            if op in ("DIV", "FLOORDIV", "MOD") and right == 0:
                raise RuntimeError(f"Line {line}: division by zero")
            if op == "POW" and (
                type(right) not in (int, float) or abs(right) > 100
            ):
                raise RuntimeError(f"Line {line}: exponent limit exceeded")
            try:
                stack.append(safe_value(BINARY[op](left, right), line))
            except Exception as exc:
                raise RuntimeError(f"Line {line}: {exc}") from exc

        elif op in COMPARE:
            right, left = pop(), pop()
            stack.append(COMPARE[op](left, right))

        elif op in ("POS", "NEG"):
            value = pop()
            if type(value) not in (int, float):
                raise RuntimeError(f"Line {line}: numeric value required")
            stack.append(+value if op == "POS" else -value)

        elif op in EXT_OPS:
            run_ext(op, item, stack, line, pop)

        elif op == "JUMP":
            next_ip = item["target"]

        elif op == "JUMP_IF_FALSE":
            if not pop():
                next_ip = item["target"]

        elif op == "REPEAT_INIT":
            count = pop()
            if type(count) not in (int, float) or int(count) != count:
                raise RuntimeError(f"Line {line}: loop count must be an integer")
            if count < 0 or count > 10000:
                raise RuntimeError(f"Line {line}: loop count out of range")
            loops[-1][ip] = int(count)

        elif op == "REPEAT_CHECK":
            # REPEAT_INIT is immediately before the loop start.
            init_pc = ip - 1
            count = loops[-1].get(init_pc, 0)
            if count <= 0:
                next_ip = item["target"]

        elif op == "REPEAT_NEXT":
            check_pc = item["target"] + 1
            init_pc = check_pc - 2
            if init_pc not in loops[-1]:
                raise RuntimeError(f"Line {line}: missing loop state")
            loops[-1][init_pc] -= 1
            next_ip = item["target"]

        elif op == "CALL":
            name = item["name"]
            info = functions.get(name)
            if not isinstance(info, dict):
                raise RuntimeError(f"Line {line}: function not found: {name}")
            argc = item["argc"]
            args = [pop() for _ in range(argc)][::-1]
            params = info["params"]
            if len(args) != len(params):
                raise RuntimeError(f"Line {line}: argument mismatch")
            if len(frames) >= 100:
                raise RuntimeError(f"Line {line}: call depth exceeded")
            frames.append({
                "return_ip": next_ip,
                "locals": dict(zip(params, args)),
            })
            loops.append({})
            next_ip = info["target"]

        elif op == "RETURN":
            result = pop()
            if not frames:
                raise RuntimeError(f"Line {line}: RETURN without CALL")
            frame = frames.pop()
            loops.pop()
            stack.append(result)
            next_ip = frame["return_ip"]

        else:
            raise RuntimeError(f"Line {line}: unknown opcode {op}")

        ip = next_ip

    if frames:
        raise RuntimeError("Program ended with unfinished function call")
    if stack:
        raise RuntimeError("Program ended with invalid stack state")

def main():
    if len(sys.argv) != 2:
        print("Usage: python compiler/vm.py build/file.bc.json")
        return 2
    try:
        program = json.loads(
            Path(sys.argv[1]).read_text(encoding="utf-8")
        )
        run(program)
        print("PASS: BB-VM execution completed")
        return 0
    except Exception as exc:
        print("VM ERROR:", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
