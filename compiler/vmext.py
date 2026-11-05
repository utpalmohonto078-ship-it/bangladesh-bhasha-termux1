EXT_OPS = {"LEN", "TOSTR", "TONUM", "LIST_ADD", "BUILD_LIST", "INDEX", "INPUT", "LIST_SET"}
MAX_LIST = 10000

def _err(line, msg):
    raise RuntimeError(f"Line {line}: {msg}")

def _build(item, stack, line, pop):
    n = item["count"]
    if n > MAX_LIST:
        _err(line, "list too large")
    stack.append([pop() for _ in range(n)][::-1])

def _index(item, stack, line, pop):
    idx = pop()
    obj = pop()
    if type(obj) not in (str, list):
        _err(line, "only text or list can be indexed")
    if type(idx) is not int:
        _err(line, "index must be an integer")
    if not -len(obj) <= idx < len(obj):
        _err(line, "index out of range")
    stack.append(obj[idx])

def _len(item, stack, line, pop):
    v = pop()
    if type(v) not in (str, list):
        _err(line, "length needs text or list")
    stack.append(len(v))

def _tostr(item, stack, line, pop):
    s = str(pop())
    if len(s) > 100000:
        _err(line, "string limit exceeded")
    stack.append(s)

def _tonum(item, stack, line, pop):
    v = pop()
    if type(v) in (int, float):
        stack.append(v)
        return
    if type(v) is not str:
        _err(line, "cannot convert to number")
    try:
        n = int(v)
    except ValueError:
        try:
            n = float(v)
        except ValueError:
            _err(line, f"cannot convert {v!r} to number")
        if n != n or abs(n) > 1e100:
            _err(line, "numeric limit exceeded")
    stack.append(n)

def _add(item, stack, line, pop):
    x = pop()
    lst = pop()
    if type(lst) is not list:
        _err(line, "first argument must be a list")
    if len(lst) >= MAX_LIST:
        _err(line, "list too large")
    stack.append(lst + [x])

def _input(item, stack, line, pop):
    prompt = pop()
    if type(prompt) is not str:
        _err(line, "prompt must be text")
    try:
        text = input(prompt)
    except EOFError:
        _err(line, "no input available")
    if len(text) > 100000:
        _err(line, "string limit exceeded")
    stack.append(text)

def _lset(item, stack, line, pop):
    val = pop()
    idx = pop()
    lst = pop()
    if type(lst) is not list:
        _err(line, "first argument must be a list")
    if type(idx) is not int:
        _err(line, "index must be an integer")
    if not -len(lst) <= idx < len(lst):
        _err(line, "index out of range")
    out = list(lst)
    out[idx] = val
    stack.append(out)

_HANDLERS = {
    "INPUT": _input,
    "LIST_SET": _lset,
    "BUILD_LIST": _build, "INDEX": _index, "LEN": _len,
    "TOSTR": _tostr, "TONUM": _tonum, "LIST_ADD": _add,
}

def run_ext(op, item, stack, line, pop):
    _HANDLERS[op](item, stack, line, pop)
