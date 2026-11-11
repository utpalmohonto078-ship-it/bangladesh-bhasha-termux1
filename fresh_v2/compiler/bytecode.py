from runtime.bytecode_validation import validate_program


def compile_ir(ir):
    validate_program(
        ir,
        expected_format="BB-V2-IR",
        instructions_key="instructions",
    )

    code = ir["instructions"]
    functions = ir.get("functions", {})

    copied_functions = {
        name: {
            "target": info["target"],
            "params": list(info["params"]),
            "globals": list(info.get("globals", [])),
        }
        for name, info in functions.items()
    }

    return {
        "format": "BB-V2-BC",
        "code": [dict(item) for item in code],
        "functions": copied_functions,
    }
