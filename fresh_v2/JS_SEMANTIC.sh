#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
mkdir -p ~/bb_backups
tar czf ~/bb_backups/pre_js_semantic_$(date +%Y%m%d_%H%M%S).tgz js
cp js/check_semantic.js js/check_semantic.js.bak_sem

python3 - <<'PY' > js/builtins.json
import json
from runtime.stdlib import BUILTINS
print(json.dumps({k: v[0] for k, v in BUILTINS.items()}, ensure_ascii=False))
PY
[ -s js/builtins.json ] || { echo "builtins.json তৈরি হয়নি"; exit 1; }
echo "builtins: $(cat js/builtins.json)"

cat > js/semantic.js <<'JSEOF'
"use strict";
const builtins = require("./builtins.json");
const { checkTypes, BBTypeError } = require("./type_checker.js");
const err = (m) => { throw new BBTypeError(m); };
const isBuiltin = (n) => Object.prototype.hasOwnProperty.call(builtins, n);

function analyze(program) {
  const topGlobals = new Set();
  const functions = new Map();
  for (const s of program.statements) {
    if (s.t === "Declare") {
      if (topGlobals.has(s.name)) err(`Duplicate variable: ${s.name}`);
      topGlobals.add(s.name);
    } else if (s.t === "Function") {
      if (functions.has(s.name)) err(`Duplicate function: ${s.name}`);
      functions.set(s.name, s);
    }
  }

  function collectGlobals(body, res) {
    for (const s of body) {
      if (s.t === "Global") res.add(s.name);
      else if (s.t === "If") { collectGlobals(s.body, res); collectGlobals(s.otherwise, res); }
      else if (s.t === "Repeat" || s.t === "While") collectGlobals(s.body, res);
    }
  }
  function collectLocals(body, res) {
    for (const s of body) {
      if (s.t === "Declare") res.add(s.name);
      else if (s.t === "If") { collectLocals(s.body, res); collectLocals(s.otherwise, res); }
      else if (s.t === "Repeat" || s.t === "While") collectLocals(s.body, res);
    }
  }

  function expression(n, scope, inFn, initMode = false) {
    switch (n.t) {
      case "Variable":
        if (initMode) { if (!scope.has(n.name)) err(`Undefined variable: ${n.name}`); }
        else if (!scope.has(n.name) && !topGlobals.has(n.name)) err(`Undefined variable: ${n.name}`);
        break;
      case "Call": {
        let expected;
        if (functions.has(n.name)) expected = functions.get(n.name).params.length;
        else if (isBuiltin(n.name)) expected = builtins[n.name];
        else err(`Unknown function: ${n.name}`);
        if (n.args.length !== expected)
          err(`${n.name}: expected ${expected} arguments, got ${n.args.length}`);
        for (const a of n.args) expression(a, scope, inFn, initMode);
        break;
      }
      case "Binary":
        expression(n.left, scope, inFn, initMode);
        expression(n.right, scope, inFn, initMode);
        break;
      case "Unary":
        expression(n.operand, scope, inFn, initMode);
        break;
      case "Number": case "String": case "Boolean": break;
      default: err(`Unsupported expression: ${n.t}`);
    }
  }

  function statements(body, scope, inFn, dg, depth = 0) {
    for (const s of body) {
      switch (s.t) {
        case "Declare":
          if (scope.has(s.name)) err(`Duplicate local variable: ${s.name}`);
          if (dg.has(s.name)) err(`${s.name} is declared GLOBAL`);
          expression(s.value, scope, inFn);
          scope.add(s.name);
          break;
        case "Assign":
          if (!scope.has(s.name) && !dg.has(s.name) && (inFn || !topGlobals.has(s.name)))
            err(`Assignment to undeclared variable: ${s.name}`);
          expression(s.value, scope, inFn);
          break;
        case "Print": expression(s.value, scope, inFn); break;
        case "If":
          expression(s.condition, scope, inFn);
          statements(s.body, scope, inFn, dg, depth);
          statements(s.otherwise, scope, inFn, dg, depth);
          break;
        case "Repeat":
          expression(s.count, scope, inFn);
          statements(s.body, scope, inFn, dg, depth + 1);
          break;
        case "While":
          expression(s.condition, scope, inFn);
          statements(s.body, scope, inFn, dg, depth + 1);
          break;
        case "Break": case "Continue":
          if (depth === 0) throw new SyntaxError("BREAK/CONTINUE outside loop");
          break;
        case "Return":
          if (!inFn) throw new SyntaxError("RETURN outside function");
          expression(s.value, scope, inFn);
          break;
        case "Global":
          if (!inFn) throw new SyntaxError("GLOBAL outside function");
          if (!topGlobals.has(s.name)) err(`Unknown global variable: ${s.name}`);
          break;
      }
    }
  }

  const inter = (a, b) => [...a].some((x) => b.has(x));
  for (const s of program.statements) {
    if (s.t === "Function") {
      const g = new Set(); collectGlobals(s.body, g);
      const params = new Set(s.params);
      if (inter(g, params)) throw new SyntaxError("GLOBAL cannot conflict with a parameter");
      const locals = new Set(s.params); collectLocals(s.body, locals);
      if (inter(g, locals)) throw new SyntaxError("GLOBAL cannot conflict with a local variable");
      statements(s.body, new Set(s.params), true, g);
    } else if (s.t !== "Declare") {
      statements([s], new Set(), false, new Set());
    }
  }

  const scope = new Set();
  for (const s of program.statements)
    if (s.t === "Declare") { expression(s.value, scope, false, true); scope.add(s.name); }

  checkTypes(program);
  return true;
}
module.exports = { analyze };
JSEOF

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

D=cpp/cases/sem; mkdir -p $D
printf 'দেখাও y\n' > $D/s1_undef.bb
printf 'দেখাও foo(1)\n' > $D/s2_unknown_fn.bb
printf 'থামো\n' > $D/s3_break.bb
printf 'ফেরত 1\n' > $D/s4_return.bb
printf 'ফাংশন f(a)\nফেরত a\nশেষ\nফাংশন f(b)\nফেরত b\nশেষ\n' > $D/s5_dupfn.bb
printf 'ফাংশন f(a)\nগ্লোবাল a\nশেষ\n' > $D/s6_global_param.bb
printf 'z = 1\n' > $D/s7_assign_undecl.bb
printf 'সংখ্যা x = 1\nগ্লোবাল x\n' > $D/s8_global_outside.bb
printf 'দেখাও দৈর্ঘ্য(1, 2)\n' > $D/s9_builtin_arity.bb

norm() { if [ "$2" -eq 0 ]; then echo OK; else
  echo "ERR|$(echo "$1" | head -1 | sed -e 's/^SEMANTIC_ERROR: //' -e 's/^Error: //')"; fi; }

pass=0; fail=0
for f in cpp/cases/err_*.bb cpp/cases/infer/t4_argcount.bb cpp/cases/sem/*.bb js/cases/ifelse.bb; do
  [ -f "$f" ] || continue
  po=$(./bhasha check "$f" 2>&1); pr=$?
  co=$(./cpp/check_semantic < "$f" 2>&1); cr=$?
  jo=$(node js/check_semantic.js < "$f" 2>&1); jr=$?
  P=$(norm "$po" $pr); C=$(norm "$co" $cr); J=$(norm "$jo" $jr)
  if [ "$P" = "$C" ] && [ "$P" = "$J" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ${P:0:55}"
  else
    fail=$((fail+1)); echo "অমিল  $f"
    echo "   Python: $P"; echo "   C++:    $C"; echo "   JS:     $J"
  fi
done
echo "== পাস $pass / ফেল $fail =="
if [ $fail -eq 0 ]; then
  git add -A && git commit -qm "js semantic layer + 3-way parity for err/sem cases" && echo "কমিট হয়েছে"
else
  cp js/check_semantic.js.bak_sem js/check_semantic.js
  echo "check_semantic.js আগের অবস্থায় ফেরানো হয়েছে; অমিলগুলো পেস্ট করুন"
fi
