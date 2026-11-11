import re
from dataclasses import dataclass

@dataclass
class Token:
    kind: str
    value: str
    line: int
    column: int

PATTERN = re.compile(
    r'(?P<SPACE>[ \t]+)|'
    r'(?P<NUMBER>\d+(?:\.\d+)?)|'
    r'(?P<STRING>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|'
    r'(?P<IDENT>[^\W\d][\w\u0980-\u09FF]*)|'
    r'(?P<OP>==|!=|<=|>=|[+\-*/%=<>(),\[\]{}:])|'
    r'(?P<NEWLINE>\n)|'
    r'(?P<COMMENT>\#.*)',
    re.UNICODE
)

KEYWORDS = {
    "সংখ্যা": "LET", "let": "LET", "var": "LET",
    "দেখাও": "PRINT", "print": "PRINT",
    "সত্য": "TRUE", "true": "TRUE",
    "মিথ্যা": "FALSE", "false": "FALSE",
    "যদি": "IF", "if": "IF",
    "নাহলে": "ELSE", "else": "ELSE",
    "শেষ": "END", "end": "END",
    "পুনরাবৃত্তি": "REPEAT", "repeat": "REPEAT",
    "ফাংশন": "FUNCTION", "function": "FUNCTION",
    "ফেরত": "RETURN", "return": "RETURN",
    "গ্লোবাল": "GLOBAL", "global": "GLOBAL",
    "যতক্ষণ": "WHILE", "while": "WHILE",
    "থামো": "BREAK", "break": "BREAK",
    "চালিয়ে_যাও": "CONTINUE", "continue": "CONTINUE",
}

def tokenize(source):
    tokens = []
    line = column = 1
    pos = 0

    while pos < len(source):
        match = PATTERN.match(source, pos)
        if not match:
            raise SyntaxError(
                f"Line {line}, column {column}: "
                f"invalid character {source[pos]!r}"
            )

        kind = match.lastgroup
        value = match.group()

        if kind == "NEWLINE":
            tokens.append(Token("NEWLINE", value, line, column))
            line += 1
            column = 1
        else:
            if kind not in ("SPACE", "COMMENT"):
                if kind == "IDENT":
                    kind = KEYWORDS.get(value, "IDENT")
                tokens.append(Token(kind, value, line, column))
            column += len(value)

        pos = match.end()

    tokens.append(Token("EOF", "", line, column))
    return tokens
