from debugger import run_debugger


def sample_program():
    return {
        "format": "BB-V2-BC",
        "code": [
            {"op": "CONST", "value": 7},
            {"op": "STORE", "name": "x"},
            {"op": "LOAD", "name": "x"},
            {"op": "PRINT"},
        ],
    }


def test_debugger_step_and_inspection():
    commands = iter(["s", "v", "s", "stack", "s", "s"])
    messages = []

    result = run_debugger(
        sample_program(),
        command_fn=lambda prompt: next(commands),
        output_fn=messages.append,
    )

    assert result is True
    assert any("Global variables" in m for m in messages)
    assert any("Stack:" in m for m in messages)
    assert "7" in messages


def test_debugger_continue():
    messages = []

    result = run_debugger(
        sample_program(),
        command_fn=lambda prompt: "continue",
        output_fn=messages.append,
    )

    assert result is True
    assert "7" in messages


def test_debugger_quit():
    messages = []

    result = run_debugger(
        sample_program(),
        command_fn=lambda prompt: "quit",
        output_fn=messages.append,
    )

    assert result is False
    assert any("বন্ধ" in m for m in messages)
