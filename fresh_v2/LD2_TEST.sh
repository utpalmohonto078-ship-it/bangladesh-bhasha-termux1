#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
export TMPDIR=${TMPDIR:-$HOME/tmp}; mkdir -p "$TMPDIR"
BK=$(cat ~/bb_backups/last_listdict)
restore() { cp -r "$BK/compiler/." compiler/; cp -r "$BK/runtime/." runtime/; echo ">> রিস্টোর হয়েছে"; }
snap() { : > "$1"; while read -r f; do
  c=$(timeout 10 ./bhasha check "$f" 2>&1 </dev/null); k=$?
  r=$(timeout 10 ./bhasha run "$f" 2>&1 </dev/null | head -c 3000 | sed 's/দৈর্ঘ্য() .*গ্রহণ করে/LEN_MSG/')
  echo "$f|$k|$(echo "$c" | head -1)|$(echo "$r" | md5sum | cut -c1-8)" >> "$1"
done < "$BK/cases.txt"; }

python3 - <<'PY' || { restore; exit 1; }
import subprocess, tempfile, os, sys
T = [
 ("literal", "সংখ্যা xs = [1, 2, 3]\nদেখাও xs\n", "out", "[1, 2, 3]"),
 ("empty_len", "সংখ্যা xs = []\nদেখাও দৈর্ঘ্য(xs)\n", "out", "0"),
 ("index_read", "সংখ্যা xs = [10, 20, 30]\nদেখাও xs[1]\n", "out", "20"),
 ("index_assign", "সংখ্যা xs = [1, 2]\nxs[0] = 9\nদেখাও xs\n", "out", "[9, 2]"),
 ("nested", "সংখ্যা m = [[1, 2], [3, 4]]\nদেখাও m[1][0]\n", "out", "3"),
 ("dict_read", 'সংখ্যা d = {"a": 1, "b": 2}\nদেখাও d["b"]\n', "out", "2"),
 ("dict_set", 'সংখ্যা d = {"a": 1}\nd["c"] = 5\nদেখাও d["c"]\n', "out", "5"),
 ("dict_len", 'দেখাও দৈর্ঘ্য({"a": 1, "b": 2})\n', "out", "2"),
 ("append_pure", "সংখ্যা xs = [1]\nসংখ্যা ys = যোগ_করো(xs, 2)\nদেখাও ys\nদেখাও xs\n", "out", "[1, 2]\n[1]"),
 ("keys", 'দেখাও চাবি({"x": 1})\n', "out", "['x']"),
 ("type_of", "সংখ্যা xs = [1]\nদেখাও ধরন(xs)\n", "out", "list"),
 ("string_index", 'সংখ্যা s = "abc"\nদেখাও s[1]\n', "out", "b"),
 ("param", "ফাংশন f(xs)\n  ফেরত xs[0]\nশেষ\nদেখাও f([7, 8])\n", "out", "7"),
 ("global_mutate", "সংখ্যা xs = [1, 2]\nফাংশন f()\n  গ্লোবাল xs\n  xs[0] = 5\n  ফেরত xs[0]\nশেষ\nদেখাও f()\n", "out", "5"),
 ("loop_build", "সংখ্যা xs = []\nসংখ্যা i = 0\nযতক্ষণ i < 3\n  xs = যোগ_করো(xs, i * 2)\n  i = i + 1\nশেষ\nদেখাও xs\n", "out", "[0, 2, 4]"),
 ("print_snapshot", "সংখ্যা xs = [1]\nদেখাও xs\nxs[0] = 2\nদেখাও xs\n", "out", "[1]\n[2]"),
 ("str_len", 'দেখাও দৈর্ঘ্য("abc")\n', "out", "3"),
 ("oob", "সংখ্যা xs = [1]\nদেখাও xs[5]\n", "err", "ইনডেক্স সীমার বাইরে"),
 ("negative", "সংখ্যা xs = [1]\nদেখাও xs[-1]\n", "err", "ইনডেক্স সীমার বাইরে"),
 ("missing_key", 'সংখ্যা d = {"a": 1}\nদেখাও d["z"]\n', "err", "চাবি নেই"),
 ("idx_type", 'সংখ্যা xs = [1]\nদেখাও xs["a"]\n', "err", "Index must be integer"),
 ("float_key", "সংখ্যা d = {1.5: 2}\n", "err", "Dict key must be string or integer"),
 ("bool_key", "সংখ্যা d = {সত্য: 1}\n", "err", "Dict key must be string or integer"),
 ("index_int", "সংখ্যা n = 5\nদেখাও n[0]\n", "err", "Cannot index integer"),
 ("retype", "সংখ্যা xs = [1]\nxs = 5\n", "err", "cannot assign integer to list"),
 ("mul_limit", "সংখ্যা xs = [[1, 2]]\nদেখাও দৈর্ঘ্য(xs[0] * 1000000)\n", "err", "List অতিরিক্ত বড়"),
 ("double_limit", "সংখ্যা a = [[1]]\nসংখ্যা i = 0\nযতক্ষণ i < 40\n  a = [a[0] + a[0]]\n  i = i + 1\nশেষ\n", "err", "List অতিরিক্ত বড়"),
]
ok = bad = 0
for name, src, kind, exp in T:
    with tempfile.NamedTemporaryFile("w", suffix=".bb", delete=False, encoding="utf-8") as f:
        f.write(src); path = f.name
    p = subprocess.run(["./bhasha", "run", path], capture_output=True, text=True, timeout=30)
    os.unlink(path)
    out = (p.stdout + p.stderr).strip()
    good = (p.stdout.strip() == exp) if kind == "out" else (exp in out)
    if good: ok += 1; print("পাস  ", name)
    else:
        bad += 1; print("ফেল  ", name, "| প্রত্যাশিত:", repr(exp)); print("      পেয়েছি:", repr(out[-200:]))
print("== নতুন টেস্ট: পাস", ok, "/ ফেল", bad, "==")
sys.exit(1 if bad else 0)
PY

snap "$BK/after.txt"
if diff "$BK/base.txt" "$BK/after.txt" > "$BK/diff.txt"; then
  echo "রিগ্রেশন: পুরোনো কেসে কোনো পরিবর্তন নেই"
else
  echo "রিগ্রেশন অমিল:"; head -20 "$BK/diff.txt"; restore; exit 1
fi
echo "Python-JS lexer তুলনা (শুধু তথ্য): $(bash js/cmp.sh tokens 2>&1 | tail -1)"
git add -A && git commit -qm "python pipeline: list and dictionary (lexer to vm) with tests" && echo "কমিট হয়েছে"
