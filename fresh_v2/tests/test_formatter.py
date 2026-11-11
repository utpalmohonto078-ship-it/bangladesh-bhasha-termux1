from formatter import format_source


def test_adds_final_newline():
    assert format_source("লিখো 25") == "লিখো 25\n"


def test_normalizes_windows_line_endings():
    assert format_source("a\r\nb\r\n") == "a\nb\n"


def test_normalizes_old_mac_line_endings():
    assert format_source("a\rb\r") == "a\nb\n"


def test_preserves_existing_newline():
    assert format_source("a\n") == "a\n"


def test_empty_source():
    assert format_source("") == ""


def test_preserves_indentation():
    source = "যদি সত্য:\n    লিখো 25\n"
    assert format_source(source) == source


def test_preserves_string_whitespace():
    source = 'লিখো "A  B"\n'
    assert format_source(source) == source
