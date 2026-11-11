#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
export TMPDIR=${TMPDIR:-$HOME/tmp}; mkdir -p "$TMPDIR" ~/bb_backups
BK=~/bb_backups/pre_listdict_$(date +%Y%m%d_%H%M%S); mkdir -p "$BK"
cp -r compiler runtime "$BK/"; echo "$BK" > ~/bb_backups/last_listdict
restore() { cp -r "$BK/compiler/." compiler/; cp -r "$BK/runtime/." runtime/; echo ">> রিস্টোর হয়েছে"; }
find cpp/cases js/cases examples learning -name '*.bb' 2>/dev/null | sort > "$BK/cases.txt"
snap() { : > "$1"; while read -r f; do
  c=$(timeout 10 ./bhasha check "$f" 2>&1 </dev/null); k=$?
  r=$(timeout 10 ./bhasha run "$f" 2>&1 </dev/null | head -c 3000 | sed 's/দৈর্ঘ্য() .*গ্রহণ করে/LEN_MSG/')
  echo "$f|$k|$(echo "$c" | head -1)|$(echo "$r" | md5sum | cut -c1-8)" >> "$1"
done < "$BK/cases.txt"; }
snap "$BK/base.txt"; echo "বেসলাইন: $(wc -l < "$BK/cases.txt") কেস"

python3 - <<'PY' || { echo "প্যাচ হয়নি, কিছু বদলায়নি"; exit 1; }
import sys
E = []
def rep(p, old, new): E.append((p, old, new))
def before(p, a, ind, L):
    E.append((p, a, "\n".join([L[0]] + [ind + l for l in L[1:]]) + "\n" + ind + a))
def after(p, a, ind, L):
    E.append((p, a, a + "\n" + "\n".join(ind + l for l in L)))
S8 = " " * 8; S12 = " " * 12; S16 = " " * 16; S20 = " " * 20

rep("compiler/lexer.py", r"[+\-*/%=<>(),])|", r"[+\-*/%=<>(),\[\]{}:])|")

before("compiler/parser.py", 'if kind == "IDENT":', S8, [
 'if kind == "IDENT" and self.tokens[self.pos + 1].kind == "OP" and self.tokens[self.pos + 1].value == "[":',
 '    name = self.advance().value',
 '    self.advance()',
 '    index = self.expression()',
 '    self.expect_op("]")',
 '    self.expect_op("=")',
 '    return A.IndexAssign(name, index, self.expression())', ''])
after("compiler/parser.py", 'while True:', S12, [
 'if (self.current().kind == "OP"',
 '        and self.current().value == "["):',
 '    self.advance()',
 '    index = self.expression()',
 '    self.expect_op("]")',
 '    left = A.Index(left, index)',
 '    continue', ''])
before("compiler/parser.py", 'if token.kind == "OP" and token.value == "(":', S8, [
 'if token.kind == "OP" and token.value == "[":',
 '    items = []',
 '    if not (self.current().kind == "OP" and self.current().value == "]"):',
 '        items.append(self.expression())',
 '        while self.current().kind == "OP" and self.current().value == ",":',
 '            self.advance()',
 '            items.append(self.expression())',
 '    self.expect_op("]")',
 '    return A.ListLit(items)', '',
 'if token.kind == "OP" and token.value == "{":',
 '    keys, values = [], []',
 '    if not (self.current().kind == "OP" and self.current().value == "}"):',
 '        keys.append(self.expression())',
 '        self.expect_op(":")',
 '        values.append(self.expression())',
 '        while self.current().kind == "OP" and self.current().value == ",":',
 '            self.advance()',
 '            keys.append(self.expression())',
 '            self.expect_op(":")',
 '            values.append(self.expression())',
 '    self.expect_op("}")',
 '    return A.DictLit(keys, values)', ''])

before("compiler/semantic.py", 'elif not isinstance(node, (A.Number, A.String, A.Boolean)):', S8, [
 'elif isinstance(node, A.ListLit):',
 '    for element in node.items:',
 '        expression(element, scope, in_function, init_mode)', '',
 'elif isinstance(node, A.DictLit):',
 '    for element in node.keys + node.values:',
 '        expression(element, scope, in_function, init_mode)', '',
 'elif isinstance(node, A.Index):',
 '    expression(node.target, scope, in_function, init_mode)',
 '    expression(node.index, scope, in_function, init_mode)', ''])
before("compiler/semantic.py", 'elif isinstance(stmt, A.Print):', S12, [
 'elif isinstance(stmt, A.IndexAssign):',
 '    if (stmt.name not in scope and stmt.name not in declared_globals',
 '        and (in_function or stmt.name not in top_globals)):',
 '        raise NameError(f"Assignment to undeclared variable: {stmt.name}")',
 '    expression(stmt.index, scope, in_function)',
 '    expression(stmt.value, scope, in_function)', ''])

before("compiler/type_checker.py", 'if isinstance(node, A.Call):', S8, [
 'if isinstance(node, A.ListLit):',
 '    for element in node.items:',
 '        infer(element, scope)',
 '    return "list"', '',
 'if isinstance(node, A.DictLit):',
 '    for element in node.keys:',
 '        key_type = infer(element, scope)',
 '        if key_type not in ("integer", "string", UNKNOWN):',
 '            raise TypeError(f"Dict key must be string or integer, got {key_type}")',
 '    for element in node.values:',
 '        infer(element, scope)',
 '    return "dict"', '',
 'if isinstance(node, A.Index):',
 '    container = infer(node.target, scope)',
 '    key_type = infer(node.index, scope)',
 '    if container not in (UNKNOWN, "list", "dict", "string"):',
 '        raise TypeError(f"Cannot index {container}")',
 '    if container in ("list", "string") and key_type not in ("integer", UNKNOWN):',
 '        raise TypeError(f"Index must be integer, got {key_type}")',
 '    return "string" if container == "string" else UNKNOWN', ''])
before("compiler/type_checker.py", 'elif isinstance(stmt, A.Print):', S12, [
 'elif isinstance(stmt, A.IndexAssign):',
 '    infer(stmt.value, scope)',
 '    key_type = infer(stmt.index, scope)',
 '    target_type = scope.get(stmt.name, globals_types.get(stmt.name, UNKNOWN))',
 '    if target_type not in (UNKNOWN, "list", "dict"):',
 '        raise TypeError(f"Cannot index-assign {target_type}")',
 '    if target_type == "list" and key_type not in ("integer", UNKNOWN):',
 '        raise TypeError(f"Index must be integer, got {key_type}")', ''])

before("compiler/ir.py", 'elif isinstance(node, A.Call):', S8, [
 'elif isinstance(node, A.ListLit):',
 '    for element in node.items:',
 '        expr(element)',
 '    code.append({"op": "BUILD_LIST", "count": len(node.items)})',
 'elif isinstance(node, A.DictLit):',
 '    for key, value in zip(node.keys, node.values):',
 '        expr(key)',
 '        expr(value)',
 '    code.append({"op": "BUILD_DICT", "count": len(node.keys)})',
 'elif isinstance(node, A.Index):',
 '    expr(node.target)',
 '    expr(node.index)',
 '    code.append({"op": "INDEX"})'])
before("compiler/ir.py", 'elif isinstance(stmt, A.Print):', S12, [
 'elif isinstance(stmt, A.IndexAssign):',
 '    code.append({"op": "LOAD", "name": stmt.name})',
 '    expr(stmt.index)',
 '    expr(stmt.value)',
 '    code.append({"op": "STORE_INDEX"})', ''])

rep("compiler/bytecode.py", '"CALL", "RETURN", "JUMP", "JUMP_IF_FALSE",',
    '"CALL", "RETURN", "JUMP", "JUMP_IF_FALSE", "BUILD_LIST", "BUILD_DICT", "INDEX", "STORE_INDEX",')

rep("runtime/vm.py", "from .stdlib import BUILTINS", "import copy\nfrom .stdlib import BUILTINS, MAX_COLLECTION")
rep("runtime/vm.py", "self.output.append(self.pop())", "self.output.append(copy.deepcopy(self.pop()))")
before("runtime/vm.py", 'result = operations[operator]()', S20, [
 'if operator == "*":',
 '    for x, y in ((left, right), (right, left)):',
 '        if isinstance(x, list) and isinstance(y, int) and not isinstance(y, bool) and len(x) * max(y, 0) > MAX_COLLECTION:',
 '            raise RuntimeError("List অতিরিক্ত বড়")'])
before("runtime/vm.py", 'if isinstance(result, str) and len(result) > 1000000:', S16, [
 'if isinstance(result, list) and len(result) > MAX_COLLECTION:',
 '    raise RuntimeError("List অতিরিক্ত বড়")'])
before("runtime/vm.py", 'elif op == "PRINT":', S12, [
 'elif op == "BUILD_LIST":',
 '    count = item["count"]',
 '    if count > MAX_COLLECTION:',
 '        raise RuntimeError("List অতিরিক্ত বড়")',
 '    items = [self.pop() for _ in range(count)][::-1]',
 '    self.stack.append(items)', '',
 'elif op == "BUILD_DICT":',
 '    count = item["count"]',
 '    if count > MAX_COLLECTION:',
 '        raise RuntimeError("Dictionary অতিরিক্ত বড়")',
 '    pairs = []',
 '    for _ in range(count):',
 '        value = self.pop()',
 '        pairs.append((self.pop(), value))',
 '    mapping = {}',
 '    for key, value in reversed(pairs):',
 '        if isinstance(key, bool) or not isinstance(key, (int, str)):',
 '            raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")',
 '        mapping[key] = value',
 '    self.stack.append(mapping)', '',
 'elif op == "INDEX":',
 '    index = self.pop()',
 '    target = self.pop()',
 '    if isinstance(target, dict):',
 '        if isinstance(index, bool) or not isinstance(index, (int, str)):',
 '            raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")',
 '        if index not in target:',
 '            raise RuntimeError("Dictionary-তে চাবি নেই")',
 '        self.stack.append(target[index])',
 '    elif isinstance(target, (list, str)):',
 '        if isinstance(index, bool) or not isinstance(index, int):',
 '            raise RuntimeError("ইনডেক্স Integer হতে হবে")',
 '        if index < 0 or index >= len(target):',
 '            raise RuntimeError("ইনডেক্স সীমার বাইরে")',
 '        self.stack.append(target[index])',
 '    else:',
 '        raise RuntimeError("এই মানে ইনডেক্স করা যায় না")', '',
 'elif op == "STORE_INDEX":',
 '    value = self.pop()',
 '    index = self.pop()',
 '    target = self.pop()',
 '    if isinstance(target, dict):',
 '        if isinstance(index, bool) or not isinstance(index, (int, str)):',
 '            raise RuntimeError("Dictionary চাবি String বা Integer হতে হবে")',
 '        if index not in target and len(target) >= MAX_COLLECTION:',
 '            raise RuntimeError("Dictionary অতিরিক্ত বড়")',
 '        target[index] = value',
 '    elif isinstance(target, list):',
 '        if isinstance(index, bool) or not isinstance(index, int):',
 '            raise RuntimeError("ইনডেক্স Integer হতে হবে")',
 '        if index < 0 or index >= len(target):',
 '            raise RuntimeError("ইনডেক্স সীমার বাইরে")',
 '        target[index] = value',
 '    else:',
 '        raise RuntimeError("এই মানে ইনডেক্স-এ মান বসানো যায় না")', ''])

orig = {}
for p, old, new in E:
    orig.setdefault(p, open(p, encoding="utf-8").read())
bad = [(p, old[:45], orig[p].count(old)) for p, old, new in E if orig[p].count(old) != 1]
if bad:
    for b in bad: print("PATCH_SKIP:", b)
    sys.exit(2)
cur = dict(orig)
for p, old, new in E:
    cur[p] = cur[p].replace(old, new, 1)
for p, t in cur.items():
    open(p, "w", encoding="utf-8").write(t)
print("PATCH_OK:", len(E), "টি সম্পাদনা")
PY

cat >> compiler/ast_nodes.py <<'AST'

@dataclass
class ListLit:
    items: list

@dataclass
class DictLit:
    keys: list
    values: list

@dataclass
class Index:
    target: object
    index: object

@dataclass
class IndexAssign:
    name: str
    index: object
    value: object
AST

cat > runtime/stdlib.py <<'STD'
MAX_COLLECTION = 100000


def type_of(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "unknown"


def length(value):
    if not isinstance(value, (str, list, dict)):
        raise TypeError("দৈর্ঘ্য() শুধু String, List বা Dictionary গ্রহণ করে")
    return len(value)


def append(items, value):
    if not isinstance(items, list):
        raise TypeError("যোগ_করো() প্রথম মান List হতে হবে")
    if len(items) >= MAX_COLLECTION:
        raise RuntimeError("List অতিরিক্ত বড়")
    return items + [value]


def keys(mapping):
    if not isinstance(mapping, dict):
        raise TypeError("চাবি() শুধু Dictionary গ্রহণ করে")
    return list(mapping.keys())


BUILTINS = {
    "ধরন": (1, type_of),
    "type_of": (1, type_of),
    "দৈর্ঘ্য": (1, length),
    "length": (1, length),
    "যোগ_করো": (2, append),
    "append": (2, append),
    "চাবি": (1, keys),
    "keys": (1, keys),
}
STD

python3 -m py_compile compiler/*.py runtime/*.py || { restore; exit 1; }
echo "ব্লক ১ শেষ। এখন ব্লক ২ চালান।"
