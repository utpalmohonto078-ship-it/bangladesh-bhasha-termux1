import copy
import math
from .stdlib import BUILTINS, MAX_COLLECTION
from .bytecode_validation import validate_program

class VirtualMachine:
    def __init__(self, input_fn=None):
        self.input_fn = input if input_fn is None else input_fn
        self.variables = {}
        self.output = []
        self.stack = []
        self.frames = []

    def pop(self):
        if not self.stack:
            raise RuntimeError("Stack underflow")
        return self.stack.pop()

    def run(self, program, trace_fn=None):
        validate_program(program)
        code = program["code"]
        functions = program.get("functions", {})
        ip = 0
        steps = 0
        max_steps = 1_000_000

        while ip < len(code):
            steps += 1
            if len(self.stack) > 10000:
                raise RuntimeError("Stack limit exceeded")
            if steps > max_steps:
                raise RuntimeError("Execution step limit exceeded")

            item = code[ip]

            if trace_fn is not None:
                trace_fn(ip, item, self)

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

            elif op == "POP":
                self.pop()

            elif op == "STORE":
                value = self.pop()
                name = item["name"]
                if self.frames and name in self.frames[-1]["globals"]:
                    self.variables[name] = value
                elif self.frames:
                    self.frames[-1]["locals"][name] = value
                else:
                    self.variables[name] = value

            elif op == "BUILD_LIST":
                count = item["count"]
                if count > MAX_COLLECTION:
                    raise RuntimeError("List অতিরিক্ত বড়")
                if count > len(self.stack):
                    raise RuntimeError("Stack underflow")

                items = [self.pop() for _ in range(count)][::-1]
                self.stack.append(items)
            
            elif op == "BUILD_DICT":
                count = item["count"]
                if count > MAX_COLLECTION:
                    raise RuntimeError("Dictionary অতিরিক্ত বড়")
                required = count * 2
                if required > len(self.stack):
                    raise RuntimeError("Stack underflow")

                pairs = []
                for _ in range(count):
                    value = self.pop()
                    pairs.append((self.pop(), value))
                mapping = {}
                for key, value in reversed(pairs):
                    if isinstance(key, bool) or not isinstance(key, (int, str)):
                        raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")
                    mapping[key] = value
                self.stack.append(mapping)
            
            elif op == "INDEX":
                index = self.pop()
                target = self.pop()
                if isinstance(target, dict):
                    if isinstance(index, bool) or not isinstance(index, (int, str)):
                        raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")
                    if index not in target:
                        raise RuntimeError("Dictionary-তে চাবি নেই")
                    self.stack.append(target[index])
                elif isinstance(target, (list, str)):
                    if isinstance(index, bool) or not isinstance(index, int):
                        raise RuntimeError("ইনডেক্স Integer হতে হবে")
                    if index < 0 or index >= len(target):
                        raise RuntimeError("ইনডেক্স সীমার বাইরে")
                    self.stack.append(target[index])
                else:
                    raise RuntimeError("এই মানে ইনডেক্স করা যায় না")
            
            elif op == "STORE_INDEX":
                value = self.pop()
                index = self.pop()
                target = self.pop()
                if isinstance(target, dict):
                    if isinstance(index, bool) or not isinstance(index, (int, str)):
                        raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")
                    if index not in target and len(target) >= MAX_COLLECTION:
                        raise RuntimeError("Dictionary অতিরিক্ত বড়")
                    target[index] = value
                elif isinstance(target, list):
                    if isinstance(index, bool) or not isinstance(index, int):
                        raise RuntimeError("ইনডেক্স Integer হতে হবে")
                    if index < 0 or index >= len(target):
                        raise RuntimeError("ইনডেক্স সীমার বাইরে")
                    target[index] = value
                else:
                    raise RuntimeError("এই মানে ইনডেক্স-এ মান বসানো যায় না")
            
            elif op == "PRINT":
                self.output.append(copy.deepcopy(self.pop()))

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
                if operator == "*":
                    for x, y in ((left, right), (right, left)):
                        if isinstance(x, str) and isinstance(y, int) and not isinstance(y, bool) and len(x) * max(y, 0) > 1000000:
                            raise RuntimeError("String অতিরিক্ত বড়")
                try:
                    if operator == "*":
                        for x, y in ((left, right), (right, left)):
                            if isinstance(x, list) and isinstance(y, int) and not isinstance(y, bool) and len(x) * max(y, 0) > MAX_COLLECTION:
                                raise RuntimeError("List অতিরিক্ত বড়")
                    result = operations[operator]()
                except ZeroDivisionError:
                    raise RuntimeError("শূন্য দিয়ে ভাগ করা যায় না")
                except (TypeError, ValueError, OverflowError):
                    raise RuntimeError(f"Operator {operator}: মানের ধরন অবৈধ")
                if isinstance(result, list) and len(result) > MAX_COLLECTION:
                    raise RuntimeError("List অতিরিক্ত বড়")
                if isinstance(result, str) and len(result) > 1000000:
                    raise RuntimeError("String অতিরিক্ত বড়")
                if isinstance(result, int) and not isinstance(result, bool) and result.bit_length() > 4096:
                    raise RuntimeError("সংখ্যা অতিরিক্ত বড়")
                self.stack.append(result)

            elif op == "JUMP":
                next_ip = item["target"]

            elif op == "JUMP_IF_FALSE":
                if not self.pop():
                    next_ip = item["target"]

            elif op == "LOOP_BEGIN":
                count = self.pop()
                if isinstance(count, bool) or not isinstance(count, (int, float)):
                    raise RuntimeError("REPEAT count must be numeric")
                if isinstance(count, float) and not math.isfinite(count):
                    raise RuntimeError("REPEAT count must be a non-negative integer")
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

            elif op == "LOOP_BREAK":
                loops = self.frames[-1]["loops"] if self.frames else self.main_loops
                if not loops:
                    raise RuntimeError("LOOP_BREAK without LOOP_BEGIN")
                loops.pop()
                next_ip = item["target"]

            elif op == "CALL":
                name = item["name"]
                argc = item["argc"]

                # Validate function and arity before changing the stack.
                if name in functions:
                    info = functions[name]
                    params = info["params"]

                    if argc != len(params):
                        raise RuntimeError(f"{name}: argument mismatch")

                    if len(self.frames) >= 100:
                        raise RuntimeError("Call depth exceeded")

                elif name in ("নাও", "input"):
                    if argc not in (0, 1):
                        raise RuntimeError(
                            f"{name}: expected 0 or 1 arguments"
                        )

                elif name in BUILTINS:
                    expected, function = BUILTINS[name]
                    if argc != expected:
                        raise RuntimeError(f"{name}: argument mismatch")

                else:
                    raise RuntimeError(f"Unknown function: {name}")

                if argc > len(self.stack):
                    raise RuntimeError("Stack underflow")

                args = self.stack[-argc:] if argc else []

                if name in functions:
                    if argc:
                        del self.stack[-argc:]

                    self.frames.append({
                        "return_ip": next_ip,
                        "stack_base": len(self.stack),
                        "locals": dict(zip(params, args)),
                        "globals": set(info.get("globals", [])),
                        "loops": [],
                    })
                    next_ip = info["target"]

                elif name in ("নাও", "input"):
                    prompt = args[0] if argc == 1 else ""
                    result = self.input_fn(prompt)
                    if argc:
                        del self.stack[-argc:]
                    self.stack.append(result)

                else:
                    try:
                        result = function(*args)
                    except (TypeError, ValueError) as error:
                        raise RuntimeError(str(error)) from None

                    if argc:
                        del self.stack[-argc:]
                    self.stack.append(result)

            elif op == "RETURN":
                if not self.frames:
                    raise RuntimeError("RETURN without CALL")

                frame = self.frames[-1]

                if len(self.stack) <= frame["stack_base"]:
                    raise RuntimeError("Function return value missing")

                result = self.pop()
                frame = self.frames.pop()

                del self.stack[frame["stack_base"]:]
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
