#!/data/data/com.termux/files/usr/bin/bash
cd "$(dirname "$0")/.."
mode=${1:-tokens}
fail=0; total=0
for f in examples/*.bb learning/bn/examples/*.bb js/cases/*.bb; do
  [ -f "$f" ] || continue
  total=$((total+1))
  python js/dump_$mode.py "$f" > "$TMPDIR/py.json" 2>"$TMPDIR/py.err"
  node js/dump_$mode.js "$f" > "$TMPDIR/js.json" 2>"$TMPDIR/js.err"
  if cmp -s "$TMPDIR/py.json" "$TMPDIR/js.json"; then
    echo "মিলেছে:  $f"
  else
    echo "মেলেনি:  $f"; fail=$((fail+1))
  fi
done
echo "মোট $total, মেলেনি $fail"
exit $fail
