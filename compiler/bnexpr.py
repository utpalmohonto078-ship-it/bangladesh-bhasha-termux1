import ast
import re

_STR = re.compile(r"""("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")
_WORDS = [
    ("এবং", "and"), ("অথবা", "or"), ("নয়", "not"),
    ("সত্য", "True"), ("মিথ্যা", "False"),
]

def normalize(text):
    parts = _STR.split(text)
    for i in range(0, len(parts), 2):
        for bn, py in _WORDS:
            parts[i] = re.sub(
                r"(?<![^\s(])" + bn + r"(?![^\s)])", py, parts[i]
            )
    return "".join(parts)

def parse_expr(text, mode="eval"):
    return ast.parse(normalize(text), mode=mode)
