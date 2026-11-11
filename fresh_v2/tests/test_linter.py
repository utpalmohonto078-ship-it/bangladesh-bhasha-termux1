from linter import lint_source


def test_clean_source():
    assert lint_source("লিখো 25\n") == []


def test_trailing_spaces():
    assert any("whitespace" in msg for _, msg in lint_source("লিখো 25  \n"))


def test_tab_detection():
    assert any("Tab" in msg for _, msg in lint_source("\tলিখো 25\n"))


def test_excess_blank_lines():
    assert any("blank line" in msg for _, msg in lint_source("a\n\n\n\nb\n"))


def test_string_spaces_are_not_trimmed():
    assert lint_source('লিখো "A  B"\n') == []
