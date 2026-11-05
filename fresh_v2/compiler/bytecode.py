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
