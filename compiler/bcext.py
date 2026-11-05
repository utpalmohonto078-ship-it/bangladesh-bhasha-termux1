import ast
import unicodedata

_RAW = {
    "len": ("LEN", 1), "দৈর্ঘ্য": ("LEN", 1),
    "str": ("TOSTR", 1), "টেক্সট": ("TOSTR", 1),
    "num": ("TONUM", 1), "সংখ্যায়": ("TONUM", 1),
    "push": ("LIST_ADD", 2), "যোগ": ("LIST_ADD", 2),
}
BUILTINS = {
    unicodedata.normalize("NFKC", k): v for k, v in _RAW.items()
}

def handles(node, functions):
    if isinstance(node, (ast.List, ast.Subscript)):
        return True
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in BUILTINS
        and node.func.id not in functions
    )

def emit(node, code, line, functions, expression):
    if isinstance(node, ast.List):
        for item in node.elts:
            expression(item, code, line, functions)
        code.append({
            "op": "BUILD_LIST", "count": len(node.elts), "line": line
        })
    elif isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            raise ValueError(f"Line {line}: slices are unsupported")
        expression(node.value, code, line, functions)
        expression(node.slice, code, line, functions)
        code.append({"op": "INDEX", "line": line})
    else:
        op, argc = BUILTINS[node.func.id]
        if node.keywords or len(node.args) != argc:
            raise ValueError(
                f"Line {line}: wrong argument count for {node.func.id}"
            )
        for arg in node.args:
            expression(arg, code, line, functions)
        code.append({"op": op, "line": line})
