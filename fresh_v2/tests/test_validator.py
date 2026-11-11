from pathlib import Path
from validator import validate_source


def test_valid_program():
    source = Path("examples/hello.bb").read_text(encoding="utf-8")
    assert validate_source(source) == []


def test_invalid_program():
    assert validate_source("যদি\n") != []


def test_empty_program():
    assert validate_source("") == []
