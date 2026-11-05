#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$HOME/BANGLADESH-BHASHA-ULTIMATE"
V2="$ROOT/fresh_v2"
STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="$ROOT/backups/while-$STAMP"

mkdir -p "$BACKUP"
cd "$ROOT"

FILES=(
  fresh_v2/compiler/ast_nodes.py
  fresh_v2/compiler/lexer.py
  fresh_v2/compiler/parser.py
  fresh_v2/compiler/semantic.py
  fresh_v2/compiler/ir.py
  fresh_v2/tests/test_v2.py
)

for f in "${FILES[@]}"; do
    cp "$f" "$BACKUP/$(basename "$f").$(echo "$f" | tr '/' '_').bak"
done

rollback() {
    echo
    echo "BUILD FAILED — restoring original files"
    for f in "${FILES[@]}"; do
        cp "$BACKUP/$(basename "$f").$(echo "$f" | tr '/' '_').bak" "$f"
    done
    echo "Original files restored. Backup: $BACKUP"
}
trap rollback ERR

cd "$V2"

python - <<'PY'
from pathlib import Path

def patch(file, old, new, count=1):
    p = Path(file)
    s = p.read_text(encoding="utf-8")
    found = s.count(old)
    if found != count:
        raise RuntimeError(
            f"{file}: expected {count} matching anchor(s), found {found}"
        )
    p.write_text(s.replace(old, new, count), encoding="utf-8")
    print(f"PATCH OK: {file}")

# 1. AST
patch(
    "compiler/ast_nodes.py",
    "@dataclass\nclass Repeat:\n    count: object\n    body: list\n",
    "@dataclass\nclass Repeat:\n    count: object\n    body: list\n\n"
    "@dataclass\nclass While:\n    condition: object\n    body: list\n"
)

# 2. Lexer
patch(
    "compiler/lexer.py",
    '"গ্লোবাল": "GLOBAL", "global": "GLOBAL",',
    '"গ্লোবাল": "GLOBAL", "global": "GLOBAL",\n'
    '    "যতক্ষণ": "WHILE", "while": "WHILE",'
)

# 3. Parser
patch(
    "compiler/parser.py",
    '''        if kind == "REPEAT":
            self.advance()
            count = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Repeat(count, body)
''',
    '''        if kind == "REPEAT":
            self.advance()
            count = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Repeat(count, body)

        if kind == "WHILE":
            self.advance()
            condition = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.While(condition, body)
'''
)

# 4. Semantic: nested global collection
patch(
    "compiler/semantic.py",
    '''            elif isinstance(stmt, A.Repeat):
                collect_globals(stmt.body, result)
''',
    '''            elif isinstance(stmt, A.Repeat):
                collect_globals(stmt.body, result)
            elif isinstance(stmt, A.While):
                collect_globals(stmt.body, result)
'''
)

# 5. Semantic: nested local collection
patch(
    "compiler/semantic.py",
    '''            elif isinstance(stmt, A.Repeat):
                collect_locals(stmt.body, result)
''',
    '''            elif isinstance(stmt, A.Repeat):
                collect_locals(stmt.body, result)
            elif isinstance(stmt, A.While):
                collect_locals(stmt.body, result)
'''
)

# 6. Semantic: validate condition and body
patch(
    "compiler/semantic.py",
    '''            elif isinstance(stmt, A.Repeat):
                expression(stmt.count, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)
''',
    '''            elif isinstance(stmt, A.Repeat):
                expression(stmt.count, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)

            elif isinstance(stmt, A.While):
                expression(stmt.condition, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)
'''
)

# 7. IR: global declarations inside while
patch(
    "compiler/ir.py",
    '''            elif isinstance(stmt, A.Repeat):
                found |= globals_in(stmt.body)
''',
    '''            elif isinstance(stmt, A.Repeat):
                found |= globals_in(stmt.body)
            elif isinstance(stmt, A.While):
                found |= globals_in(stmt.body)
'''
)

# 8. IR: while loop using existing jumps
patch(
    "compiler/ir.py",
    '''            elif isinstance(stmt, A.Repeat):
                expr(stmt.count)
                begin = len(code)
                code.append({"op": "LOOP_BEGIN", "target": -1})
                block(stmt.body)
                code.append({"op": "LOOP_NEXT", "target": begin + 1})
                code[begin]["target"] = len(code)
''',
    '''            elif isinstance(stmt, A.Repeat):
                expr(stmt.count)
                begin = len(code)
                code.append({"op": "LOOP_BEGIN", "target": -1})
                block(stmt.body)
                code.append({"op": "LOOP_NEXT", "target": begin + 1})
                code[begin]["target"] = len(code)

            elif isinstance(stmt, A.While):
                begin = len(code)
                expr(stmt.condition)
                exit_jump = len(code)
                code.append({"op": "JUMP_IF_FALSE", "target": -1})
                block(stmt.body)
                code.append({"op": "JUMP", "target": begin})
                code[exit_jump]["target"] = len(code)
'''
)

# 9. Add three regression tests
patch(
    "tests/test_v2.py",
    '\nif __name__ == "__main__":',
    '''
    def test_while(self):
        src = (
            "সংখ্যা i = 0\\\\n"
            "যতক্ষণ i < 5\\\\n"
            "দেখাও i\\\\n"
            "i = i + 1\\\\n"
            "শেষ\\\\n"
        )
        self.assertEqual(run_source(src), [0, 1, 2, 3, 4])

    def test_global_inside_while(self):
        src = (
            "সংখ্যা total = 2\\\\n"
            "ফাংশন change()\\\\n"
            "সংখ্যা i = 0\\\\n"
            "যতক্ষণ i < 2\\\\n"
            "গ্লোবাল total\\\\n"
            "total = total + 1\\\\n"
            "i = i + 1\\\\n"
            "শেষ\\\\n"
            "ফেরত total\\\\n"
            "শেষ\\\\n"
            "দেখাও change()\\\\n"
            "দেখাও total\\\\n"
        )
        self.assertEqual(run_source(src), [4, 4])

    def test_while_false_initially(self):
        src = (
            "সংখ্যা i = 0\\\\n"
            "যতক্ষণ মিথ্যা\\\\n"
            "i = i + 1\\\\n"
            "দেখাও 99\\\\n"
            "শেষ\\\\n"
            "দেখাও i\\\\n"
        )
        self.assertEqual(run_source(src), [0])

if __name__ == "__main__":'''
)

print("ALL WHILE PATCHES APPLIED")
PY

echo
echo "===== PYTHON SYNTAX ====="
python -m compileall -q compiler runtime bb.py tests

echo
echo "===== V2 REGRESSION TESTS ====="
PYTHONPATH="$V2" python -m unittest discover -s tests -v

echo
echo "===== V1 + V2 COMPLETE CHECK ====="
cd "$ROOT"
if [ -f check_all.sh ]; then
    bash check_all.sh
else
    python tests/run_lang.py
    python tests/run_negative.py
    cd "$V2"
    PYTHONPATH="$V2" python -m unittest discover -s tests -v
fi

echo
echo "===== GIT STATUS ====="
cd "$ROOT"
git status -sb

echo
echo "===== BACKUP ====="
echo "$BACKUP"

trap - ERR
echo
echo "SUCCESS: WHILE IMPLEMENTATION AND REGRESSION CHECKS PASSED"
