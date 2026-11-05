#!/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE
fail=0
for f in tests/negative/*.bb; do
  name=$(basename "$f" .bb)
  if python compiler/ir.py "$f" >/dev/null 2>&1 \
     && python compiler/ir_validate.py "build/$name.ir.json" >/dev/null 2>&1 \
     && python compiler/bytecode.py "build/$name.ir.json" >/dev/null 2>&1 \
     && python compiler/vm.py "build/$name.bc.json" >/dev/null 2>&1; then
    echo "FAIL: $name should have been rejected"
    fail=1
  else
    echo "PASS: $name rejected"
  fi
done
exit $fail
