#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
H=cpp/type_checker.hpp
BK=$H.bak_top_$(date +%H%M%S)
cp $H $BK
python3 - <<'PY'
p="cpp/type_checker.hpp"
s=open(p,encoding="utf-8").read()
edits=[
("    std::set<FunctionKey> fn_active;",
 "    std::set<FunctionKey> fn_active;\n    bool skip_next_prefix = false;"),
("        auto fi = functions.find(name);\n        if (fi == functions.end()) return UNKNOWN_TYPE;",
 "        bool skip_prefix = skip_next_prefix;\n        skip_next_prefix = false;\n        auto fi = functions.find(name);\n        if (fi == functions.end()) return UNKNOWN_TYPE;"),
('            std::string sig = name + "(";',
 '            if (skip_prefix) throw;\n            std::string sig = name + "(";'),
("        check_function(entry.first, args);",
 "        skip_next_prefix = true;\n        check_function(entry.first, args);\n        skip_next_prefix = false;"),
]
for o,n in edits:
    if s.count(o)!=1:
        print("PATCH_SKIP:", repr(o[:50]), "পাওয়া গেছে", s.count(o), "বার"); raise SystemExit(2)
    s=s.replace(o,n)
open(p,"w",encoding="utf-8").write(s)
print("PATCH_OK")
PY
[ $? -ne 0 ] && { cp $BK $H; echo "রিস্টোর হয়েছে"; exit 1; }
g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic 2>build_err.txt || {
  echo "বিল্ড ফেল, রিস্টোর"; cp $BK $H; head -20 build_err.txt; exit 1; }
pass=0; fail=0
for f in cpp/cases/infer2/*.bb cpp/cases/infer/t5_argtype.bb; do
  cout=$(./cpp/check_semantic < $f 2>&1); crc=$?
  pout=$(./bhasha check $f 2>&1); prc=$?
  if [ $crc -eq 0 ] && [ $prc -eq 0 ]; then pass=$((pass+1)); echo "মিল   $(basename $f): OK"; continue; fi
  cm=$(echo "$cout" | head -1 | sed 's/^SEMANTIC_ERROR: //')
  pm=$(echo "$pout" | head -1 | sed 's/^Error: //')
  if [ $crc -ne 0 ] && [ $prc -ne 0 ] && [ "$cm" = "$pm" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ERR | $cm"
  else
    fail=$((fail+1)); echo "অমিল  $(basename $f)"; echo "   C++:    $cout"; echo "   Python: $pout"
  fi
done
echo "== পাস $pass / ফেল $fail =="
[ $fail -ne 0 ] && { cp $BK $H; g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic; echo "ফেল, আগের অবস্থায় রিস্টোর"; exit 1; }
git add -A && git commit -qm "cpp function type inference: parity with python (prefix, top pass)" && echo "কমিট হয়েছে"
