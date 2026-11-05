#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
echo "== V1 MULTILINGUAL =="; python tests/run_lang.py; echo "rc=$?"
echo "== V1 NEGATIVE =="; python tests/run_negative.py; echo "rc=$?"
echo "== V2 REGRESSION =="; (cd fresh_v2 && PYTHONPATH="$PWD" python -m unittest discover -s tests 2>&1 | tail -5)
echo "== GIT =="; git status -sb; git log -3 --format="%h %an <%ae> | %s"
