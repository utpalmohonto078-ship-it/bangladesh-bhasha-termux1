#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
cp cpp/type_checker.hpp cpp/type_checker.hpp.bak_infer_$(date +%H%M%S)
BK=$(ls -t cpp/type_checker.hpp.bak_infer_* | head -1)
g++ -std=c++17 -O1 cpp/check_semantic.cpp -Icpp -o cpp/check_semantic 2>build_err.txt || {
  echo "বিল্ড ফেল, রিস্টোর করছি"; cp "$BK" cpp/type_checker.hpp; head -20 build_err.txt; exit 1; }
D=cpp/cases/infer; mkdir -p $D
printf 'ফাংশন যোগ(a, b)\nফেরত a + b\nশেষ\nদেখাও যোগ(1, 2)\n' > $D/t1_ret.bb
printf 'ফাংশন f(a)\nযদি a > 0\nফেরত 1\nশেষ\nফেরত 2.5\nশেষ\nদেখাও f(3) + 1\n' > $D/t2_merge.bb
printf 'ফাংশন fact(n)\nযদি n < 2\nফেরত 1\nশেষ\nফেরত n * fact(n - 1)\nশেষ\nদেখাও fact(5)\n' > $D/t3_recur.bb
printf 'ফাংশন যোগ(a, b)\nফেরত a + b\nশেষ\nদেখাও যোগ(1)\n' > $D/t4_argcount.bb
printf 'ফাংশন f(a)\nফেরত a + 1\nশেষ\nদেখাও f("x")\n' > $D/t5_argtype.bb
printf 'ফাংশন f(a)\nযদি a > 0\nফেরত 1\nশেষ\nফেরত "x"\nশেষ\nদেখাও f(3) + 1\n' > $D/t6_mixed.bb
pass=0; fail=0
for f in $D/*.bb; do
  cout=$(./cpp/check_semantic < $f 2>&1); crc=$?
  pout=$(./bhasha check $f 2>&1); prc=$?
  [ $crc -eq 0 ] && cs=OK || cs=ERR
  [ $prc -eq 0 ] && ps=OK || ps=ERR
  if [ $cs = $ps ]; then pass=$((pass+1)); echo "মিল   $(basename $f): $cs"
  else fail=$((fail+1)); echo "অমিল  $(basename $f): C++=$cs Python=$ps"
       echo "   C++:    $cout"; echo "   Python: $pout"; fi
done
echo "== পাস $pass / ফেল $fail =="
