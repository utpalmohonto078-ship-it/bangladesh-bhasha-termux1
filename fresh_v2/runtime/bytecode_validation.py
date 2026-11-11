from runtime.stdlib import MAX_COLLECTION


ALLOWED_OPS = {
    "CONST", "LOAD", "STORE", "PRINT", "BINARY", "UNARY",
    "CALL", "RETURN", "JUMP", "JUMP_IF_FALSE",
    "BUILD_LIST", "BUILD_DICT", "INDEX", "STORE_INDEX",
    "LOOP_BEGIN", "LOOP_NEXT", "LOOP_BREAK", "POP",
}

JUMP_OPS = {
    "JUMP", "JUMP_IF_FALSE", "LOOP_BEGIN",
    "LOOP_NEXT", "LOOP_BREAK",
}

BINARY_OPERATORS = {
    "+", "-", "*", "/", "%", "==", "!=", "<",
    ">", "<=", ">=",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _strict_int(value):
    return type(value) is int


def validate_program(program, expected_format="BB-V2-BC",
                     instructions_key="code"):

    _require(isinstance(program, dict),
             "Program must be a dictionary")

    _require(program.get("format") == expected_format,
             "Invalid bytecode format")

    code = program.get(instructions_key)

    _require(isinstance(code, list),
             "Instructions must be a list")

    functions = program.get("functions", {})

    _require(isinstance(functions, dict),
             "Functions must be a dictionary")

    for index, item in enumerate(code):
        prefix = f"Instruction {index}"

        _require(isinstance(item, dict),
                 f"{prefix}: instruction must be a dictionary")

        op = item.get("op")

        _require(isinstance(op, str) and op in ALLOWED_OPS,
                 f"{prefix}: invalid opcode")

        if op in ("LOAD", "STORE", "CALL"):
            name = item.get("name")
            _require(
                isinstance(name, str) and bool(name.strip()),
                f"{prefix}: invalid name"
            )

        if op == "CALL":
            argc = item.get("argc")
            _require(
                _strict_int(argc) and 0 <= argc <= MAX_COLLECTION,
                f"{prefix}: invalid argument count"
            )

        if op in ("BUILD_LIST", "BUILD_DICT"):
            count = item.get("count")
            _require(
                _strict_int(count) and count >= 0,
                f"{prefix}: invalid collection count"
            )

        if op == "UNARY":
            _require(
                item.get("operator") in ("+", "-"),
                f"{prefix}: invalid unary operator"
            )

        if op == "BINARY":
            _require(
                item.get("operator") in BINARY_OPERATORS,
                f"{prefix}: invalid binary operator"
            )

        if op in JUMP_OPS:
            target = item.get("target")
            _require(
                _strict_int(target) and 0 <= target <= len(code),
                f"{prefix}: invalid jump target"
            )

    for name, info in functions.items():
        _require(
            isinstance(name, str) and bool(name.strip()),
            "Invalid function name"
        )
        _require(
            isinstance(info, dict),
            f"Invalid function metadata: {name}"
        )

        target = info.get("target")
        params = info.get("params")
        globals_list = info.get("globals", [])

        _require(
            _strict_int(target) and 0 <= target < len(code),
            f"Invalid function target: {name}"
        )

        _require(
            isinstance(params, list)
            and all(isinstance(p, str) and bool(p.strip()) for p in params)
            and len(params) == len(set(params)),
            f"Invalid function parameters: {name}"
        )

        _require(
            isinstance(globals_list, list)
            and all(isinstance(g, str) and bool(g.strip())
                    for g in globals_list)
            and len(globals_list) == len(set(globals_list)),
            f"Invalid function globals: {name}"
        )

    return True
