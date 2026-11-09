#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")/.." || exit 1

fail=0
total=0
TMPDIR="${TMPDIR:-/tmp}"

for f in examples/*.bb learning/bn/examples/*.bb; do
    [ -f "$f" ] || continue
    total=$((total + 1))

    if ! python js/dump_tokens.py "$f" > "$TMPDIR/py.json"; then
        echo "Python Error: $f"
        fail=$((fail + 1))
        continue
    fi

    if ! node js/dump_tokens.js "$f" > "$TMPDIR/js.json"; then
        echo "JavaScript Error: $f"
        fail=$((fail + 1))
        continue
    fi

    if cmp -s "$TMPDIR/py.json" "$TMPDIR/js.json"; then
        echo "মিলেছে: $f"
    else
        echo "মেলেনি: $f"
        fail=$((fail + 1))
    fi
done

echo "মোট $total, মেলেনি $fail"
exit "$fail"
