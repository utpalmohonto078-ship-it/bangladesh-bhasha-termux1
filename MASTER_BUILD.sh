#!/data/data/com.termux/files/usr/bin/bash

set -u

ROOT="$HOME/BANGLADESH-BHASHA-ULTIMATE"
cd "$ROOT" || exit 1

mkdir -p backups reports

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP="backups/master-backup-$STAMP.tar.gz"
REPORT="reports/master-report-$STAMP.txt"

exec > >(tee "$REPORT") 2>&1

echo "======================================"
echo " BANGLADESH BHASHA — ULTIMATE"
echo " MASTER BUILD & VERIFICATION"
echo "======================================"

echo
echo "[1/7] BACKUP"
tar -czf "$BACKUP" compiler tests examples
if gzip -t "$BACKUP"; then
    echo "PASS: BACKUP VERIFIED"
else
    echo "FAIL: BACKUP"
    exit 1
fi

echo
echo "[2/7] PROJECT STATUS"
git log -1 --oneline
git status --short

echo
echo "[3/7] PYTHON SYNTAX"
if python -m py_compile core/*.py compiler/*.py tests/*.py; then
    echo "PASS: PYTHON SYNTAX"
else
    echo "FAIL: PYTHON SYNTAX"
fi

echo
echo "[4/7] MULTILINGUAL TEST"
if python tests/run_lang.py; then
    echo "PASS: MULTILINGUAL"
else
    echo "FAIL: MULTILINGUAL"
fi

echo
echo "[5/7] NEGATIVE TEST"
if python tests/run_negative.py; then
    echo "PASS: NEGATIVE TESTS"
else
    echo "FAIL: NEGATIVE TESTS"
fi

echo
echo "[6/7] PROJECT INVENTORY"
find compiler core tests examples -maxdepth 3 -type f 2>/dev/null | sort

echo
echo "[7/7] GLOBAL SCOPE STATUS"
if grep -Rni 'GLOBAL' compiler/lang.py compiler/ir.py \
    compiler/ir_validate.py compiler/bytecode.py compiler/vm.py; then
    echo "GLOBAL references found; implementation needs verification."
else
    echo "PENDING: GLOBAL SCOPE implementation"
fi

echo
echo "======================================"
echo " MASTER REPORT COMPLETE"
echo "Backup: $BACKUP"
echo "Report: $REPORT"
echo "======================================"
