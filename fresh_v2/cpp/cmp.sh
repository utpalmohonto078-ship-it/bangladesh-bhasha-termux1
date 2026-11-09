#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")/.."
mode=${1:-tokens}
clang++ -std=c++17 -O2 -o cpp/dump_$mode cpp/dump_$mode.cpp || exit 1
fail=0; total=0
for f in examples/*.bb learning/bn/examples/*.bb js/cases/*.bb cpp/cases/*.bb; do
  [ -f "$f" ] || continue
  total=$((total+1))
  python js/dump_$mode.py "$f" > "$TMPDIR/py.json" 2>/dev/null
  ./cpp/dump_$mode "$f" > "$TMPDIR/cpp.json" 2>/dev/null
  if cmp -s "$TMPDIR/py.json" "$TMPDIR/cpp.json"; then
    echo "মিলেছে:  $f"
  else
    echo "মেলেনি:  $f"; fail=$((fail+1))
  fi
done
echo "মোট $total, মেলেনি $fail"
exit $fail
