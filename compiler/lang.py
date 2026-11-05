# Keyword tables. One entry per language; add a line to add a language.
LANGS = {}
LANGS["bn"] = dict(
    LET="সংখ্যা", PRINT="দেখাও", IF="যদি", ELSE="নাহলে", END="শেষ",
    REPEAT="পুনরাবৃত্তি", FUNCTION="ফাংশন", RETURN="ফেরত",
    AND="এবং", OR="অথবা", NOT="নয়", TRUE="সত্য", FALSE="মিথ্যা",
    LEN="দৈর্ঘ্য", STR="টেক্সট", NUM="সংখ্যায়", PUSH="যোগ")
LANGS["en"] = dict(
    LET="LET", PRINT="PRINT", IF="IF", ELSE="ELSE", END="END",
    REPEAT="REPEAT", FUNCTION="FUNCTION", RETURN="RETURN",
    AND="and", OR="or", NOT="not", TRUE="True", FALSE="False",
    LEN="len", STR="str", NUM="num", PUSH="push")
LANGS["ja"] = dict(
    LET="変数", PRINT="表示", IF="もし", ELSE="それ以外", END="終わり",
    REPEAT="繰り返し", FUNCTION="関数", RETURN="戻る",
    AND="かつ", OR="または", NOT="否定", TRUE="真", FALSE="偽",
    LEN="長さ", STR="文字列", NUM="数値", PUSH="追加")
LANGS["zh"] = dict(
    LET="变量", PRINT="显示", IF="如果", ELSE="否则", END="结束",
    REPEAT="重复", FUNCTION="函数", RETURN="返回",
    AND="并且", OR="或者", NOT="非", TRUE="真", FALSE="假",
    LEN="长度", STR="文本", NUM="数字", PUSH="添加")
LANGS["ko"] = dict(
    LET="변수", PRINT="출력", IF="만약", ELSE="아니면", END="끝",
    REPEAT="반복", FUNCTION="함수", RETURN="반환",
    AND="그리고", OR="또는", NOT="아님", TRUE="참", FALSE="거짓",
    LEN="길이", STR="문자열", NUM="숫자", PUSH="추가")
LANGS["fa"] = dict(
    LET="متغیر", PRINT="نمایش", IF="اگر", ELSE="وگرنه", END="پایان",
    REPEAT="تکرار", FUNCTION="تابع", RETURN="بازگشت",
    AND="و", OR="یا", NOT="نه", TRUE="درست", FALSE="نادرست",
    LEN="طول", STR="متن", NUM="عدد", PUSH="افزودن")
LANGS["ru"] = dict(
    LET="пусть", PRINT="вывод", IF="если", ELSE="иначе", END="конец",
    REPEAT="повтор", FUNCTION="функция", RETURN="вернуть",
    AND="и", OR="или", NOT="не", TRUE="истина", FALSE="ложь",
    LEN="длина", STR="строка", NUM="число", PUSH="добавить")
EXTRA = {"LET": ["লেখা", "তালিকা", "let", "var"]}
STMT_KEYS = ["LET", "PRINT", "IF", "ELSE", "END", "REPEAT",
             "FUNCTION", "RETURN"]
EXPR_KEYS = ["AND", "OR", "NOT", "TRUE", "FALSE"]
FUNC_KEYS = ["LEN", "STR", "NUM", "PUSH"]
LANGS["fa"] = dict(
    LET="متغیر", PRINT="نمایش", IF="اگر", ELSE="وگرنه", END="پایان",
    REPEAT="تکرار", FUNCTION="تابع", RETURN="بازگشت",
    AND="و", OR="یا", NOT="نه", TRUE="درست", FALSE="نادرست",
    LEN="طول", STR="متن", NUM="عدد", PUSH="افزودن")
LANGS["ru"] = dict(
    LET="пусть", PRINT="вывод", IF="если", ELSE="иначе", END="конец",
    REPEAT="повтор", FUNCTION="функция", RETURN="вернуть",
    AND="и", OR="или", NOT="не", TRUE="истина", FALSE="ложь",
    LEN="длина", STR="строка", NUM="число", PUSH="добавить")
EXTRA = {"LET": ["লেখা", "তালিকা", "let", "var"]}
STMT_KEYS = ["LET", "PRINT", "IF", "ELSE", "END", "REPEAT",
             "FUNCTION", "RETURN"]
EXPR_KEYS = ["AND", "OR", "NOT", "TRUE", "FALSE"]
FUNC_KEYS = ["LEN", "STR", "NUM", "PUSH"]

import re
import unicodedata

def _norm(word):
    return unicodedata.normalize("NFKC", word).casefold()

def _build(keys):
    table = {}
    def add(word, key):
        w = _norm(word)
        if table.get(w, key) != key:
            raise ValueError("keyword clash: " + word)
        table[w] = key
    for words in LANGS.values():
        for key in keys:
            add(words[key], key)
    for key in keys:
        for w in EXTRA.get(key, []):
            add(w, key)
    return table

_STMT = _build(STMT_KEYS)
_EXPR = _build(EXPR_KEYS)
_FUNC = _build(FUNC_KEYS)

_STR = re.compile(r"""("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")
_TOKEN = re.compile(r"[^\s()\[\],+\-*/%=<>!:]+")
_PY = {"AND": "and", "OR": "or", "NOT": "not",
       "TRUE": "True", "FALSE": "False"}
_FN = {"LEN": "len", "STR": "str", "NUM": "num", "PUSH": "push"}
_QUOTES = {0x201C: 34, 0x201D: 34}

def _protect(text, fn):
    parts = _STR.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = fn(parts[i])
    return "".join(parts)

def _clean(text):
    text = unicodedata.normalize("NFKC", text)
    out = []
    for ch in text:
        if unicodedata.category(ch) == "Nd":
            out.append(str(unicodedata.digit(ch)))
        else:
            out.append(ch)
    return "".join(out).replace("،", ",")

def _translate(text, calls):
    def repl(m):
        key = m.group(0).casefold()
        if key in _EXPR:
            return _PY[_EXPR[key]]
        if (calls and key in _FUNC
                and text[m.end():].lstrip().startswith("(")):
            return _FN[_FUNC[key]]
        return m.group(0)
    return _TOKEN.sub(repl, text)

def canonicalize_line(line):
    line = line.translate(_QUOTES)
    line = _protect(line, _clean)
    m = re.match(r"(\S+)(?:\s+(.*))?$", line, re.S)
    canon = _STMT.get(m.group(1).casefold()) if m else None
    if canon:
        rest = _protect(m.group(2) or "",
                        lambda t: _translate(t, canon != "FUNCTION"))
        return (canon + " " + rest).strip()
    return _protect(line, lambda t: _translate(t, True))

_IDX = re.compile(
    r"([^\W\d][\w\u0300-\u036F\u064B-\u065F\u0900-\u0DFF]*)"
    r"\s*\[(.+)\]\s*=(?!=)\s*(.+)")
_base_canonicalize = canonicalize_line

def canonicalize_line(line):
    line = _base_canonicalize(line)
    m = _IDX.fullmatch(line)
    if m:
        name, idx, val = m.groups()
        return f"LET {name} = set({name}, {idx}, {val})"
    return line
