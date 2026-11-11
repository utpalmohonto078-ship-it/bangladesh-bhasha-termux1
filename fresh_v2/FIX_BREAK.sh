#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
H=cpp/semantic.hpp
BK=$H.bak_break_$(date +%H%M%S)
cp $H $BK
python3 - <<'PY'
p="cpp/semantic.hpp"
s=open(p,encoding="utf-8").read()
for o in ('"BREAK outside loop"','"CONTINUE outside loop"'):
    if s.count(o)!=1:
        print("PATCH_SKIP:",o,"পাওয়া গেছে",s.count(o),"বার"); raise SystemExit(2)
    s=s.replace(o,'"BREAK/CONTINUE outside loop"')
open(p,"w",encoding="utf-8").write(s)
print("PATCH_OK")
PY
[ $? -ne 0 ] && { cp $BK $H; echo "রিস্টোর হয়েছে"; exit 1; }
g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic 2>build_err.txt || {
  echo "বিল্ড ফেল, রিস্টোর"; cp $BK $H; head -20 build_err.txt; exit 1; }

cat > js/check_semantic.js <<'JSEOF'
const { tokenize } = require("./lexer.js");
const { parse } = require("./parser.js");
const { analyze } = require("./semantic.js");
const { BBTypeError } = require("./type_checker.js");
const src = require("fs").readFileSync(0, "utf8").replace(/\r\n?/g, "\n");
try {
  analyze(parse(tokenize(src)));
  console.log("SEMANTIC_OK");
} catch (e) {
  if (e instanceof BBTypeError || e instanceof SyntaxError) {
    console.log("SEMANTIC_ERROR: " + e.message);
    process.exit(1);
  }
  throw e;
}
JSEOF

printf 'চালিয়ে_যাও\n' > cpp/cases/sem/s10_continue.bb
norm() { if [ "$2" -eq 0 ]; then echo OK; else
  echo "ERR|$(echo "$1" | head -1 | sed -e 's/^SEMANTIC_ERROR: //' -e 's/^Error: //')"; fi; }
pass=0; fail=0
for f in cpp/cases/sem/s3_break.bb cpp/cases/sem/s10_continue.bb cpp/cases/infer/t4_argcount.bb cpp/cases/infer2/n4_nested_call_err.bb; do
  po=$(./bhasha check "$f" 2>&1); pr=$?
  co=$(./cpp/check_semantic < "$f" 2>&1); cr=$?
  jo=$(node js/check_semantic.js < "$f" 2>&1); jr=$?
  P=$(norm "$po" $pr); C=$(norm "$co" $cr); J=$(norm "$jo" $jr)
  if [ "$P" = "$C" ] && [ "$P" = "$J" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ${P:0:55}"
  else
    fail=$((fail+1)); echo "অমিল  $f"; echo "   Python: $P"; echo "   C++:    $C"; echo "   JS:     $J"
  fi
done
echo "== পাস $pass / ফেল $fail =="
if [ $fail -eq 0 ]; then
  git add -A && git commit -qm "semantic parity: js semantic layer, unified BREAK/CONTINUE message in C++" && echo "কমিট হয়েছে"
else
  cp $BK $H; g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic
  echo "ফেল: semantic.hpp রিস্টোর হয়েছে; অমিলগুলো পেস্ট করুন"
fi
