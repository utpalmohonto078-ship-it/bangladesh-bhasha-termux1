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
