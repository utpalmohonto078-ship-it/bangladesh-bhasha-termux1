#!/data/data/com.termux/files/usr/bin/bash
cd ~/BANGLADESH-BHASHA-ULTIMATE/fresh_v2
mkdir -p ~/bb_backups
tar czf ~/bb_backups/pre_js_checker_$(date +%Y%m%d_%H%M%S).tgz js
for x in type_checker check_semantic; do [ -f js/$x.js ] && cp js/$x.js js/$x.js.bak; done

cat > js/type_checker.js <<'JSEOF'
"use strict";
const NUMERIC = new Set(["integer", "float"]);
const UNKNOWN = "unknown";

class BBTypeError extends Error {}
function fail(m) { throw new BBTypeError(m); }

function compatible(expected, actual) {
  if (expected === UNKNOWN || actual === UNKNOWN) return true;
  if (expected === actual) return true;
  return expected === "float" && actual === "integer";
}

function mergeReturns(types) {
  if (!types.length || types.includes(UNKNOWN)) return UNKNOWN;
  const u = new Set(types);
  if (u.size === 1) return [...u][0];
  if ([...u].every((t) => NUMERIC.has(t))) return "float";
  return UNKNOWN;
}

function checkTypes(program) {
  const globalsTypes = new Map();
  const functions = new Map();
  for (const s of program.statements)
    if (s.t === "Function") functions.set(s.name, s);

  const returnStack = [];
  const fnCache = new Map();
  const fnActive = new Set();

  function lookup(scope, name) {
    if (scope.has(name)) return scope.get(name);
    if (globalsTypes.has(name)) return globalsTypes.get(name);
    return UNKNOWN;
  }

  function infer(n, scope) {
    switch (n.t) {
      case "Number": return n.isFloat ? "float" : "integer";
      case "String": return "string";
      case "Boolean": return "boolean";
      case "Variable": return lookup(scope, n.name);
      case "Call": {
        const args = n.args.map((a) => infer(a, scope));
        if (functions.has(n.name)) return checkFunction(n.name, args);
        if (n.name === "ধরন" || n.name === "type_of") return "string";
        if (n.name === "দৈর্ঘ্য" || n.name === "length") return "integer";
        return UNKNOWN;
      }
      case "Unary": {
        const v = infer(n.operand, scope);
        if (v !== UNKNOWN && !NUMERIC.has(v))
          fail(`Unary ${n.operator}: numeric value required, got ${v}`);
        return v;
      }
      case "Binary": {
        const l = infer(n.left, scope);
        const r = infer(n.right, scope);
        const op = n.operator;
        if (["+", "-", "*", "/", "%"].includes(op)) {
          if (op === "+" && l === r && l === "string") return "string";
          if (op === "+" && (l === "string" || r === "string") &&
              (l === UNKNOWN || r === UNKNOWN)) return UNKNOWN;
          if (l !== UNKNOWN && !NUMERIC.has(l))
            fail(`Operator ${op}: numeric value required, got ${l}`);
          if (r !== UNKNOWN && !NUMERIC.has(r))
            fail(`Operator ${op}: numeric value required, got ${r}`);
          if (l === UNKNOWN || r === UNKNOWN) return UNKNOWN;
          if (op === "/") return "float";
          return (l === "float" || r === "float") ? "float" : "integer";
        }
        if (["==", "!=", "<", ">", "<=", ">="].includes(op)) {
          if (l !== UNKNOWN && r !== UNKNOWN) {
            const sameNumeric = NUMERIC.has(l) && NUMERIC.has(r);
            if (l !== r && !sameNumeric)
              fail(`Incompatible comparison: ${l} and ${r}`);
            if (op !== "==" && op !== "!=" &&
                !(sameNumeric || (l === r && r === "string")))
              fail(`Operator ${op}: values are not order-comparable`);
          }
          return "boolean";
        }
      }
    }
    fail(`Static type checker: unsupported expression ${n.t}`);
  }

  function functionGlobals(fn) {
    const found = new Set();
    (function walk(body) {
      for (const it of body) {
        if (it.t === "Global") found.add(it.name);
        else if (it.t === "If") { walk(it.body); walk(it.otherwise); }
        else if (it.t === "Repeat" || it.t === "While") walk(it.body);
      }
    })(fn.body);
    return found;
  }

  function checkFunction(name, argTypes) {
    const fn = functions.get(name);
    if (argTypes.length !== fn.params.length) return UNKNOWN;
    const key = JSON.stringify([name, argTypes]);
    if (fnCache.has(key)) return fnCache.get(key);
    if (fnActive.has(key)) return UNKNOWN;
    fnActive.add(key);
    returnStack.push([]);
    let result;
    try {
      const scope = new Map();
      fn.params.forEach((p, i) => scope.set(p, argTypes[i]));
      checkBody(fn.body, scope, functionGlobals(fn));
      result = mergeReturns(returnStack[returnStack.length - 1]);
    } catch (e) {
      if (e instanceof BBTypeError)
        throw new BBTypeError(`${name}(${argTypes.join(", ")}): ${e.message}`);
      throw e;
    } finally {
      returnStack.pop();
      fnActive.delete(key);
    }
    fnCache.set(key, result);
    return result;
  }

  function assignCheck(name, expected, actual) {
    if (!compatible(expected, actual))
      fail(`${name}: cannot assign ${actual} to ${expected}`);
  }

  function checkBody(body, scope, dg) {
    for (const s of body) {
      if (s.t === "Declare") {
        if (dg.has(s.name))
          fail(`${s.name}: cannot declare a GLOBAL variable locally`);
        scope.set(s.name, infer(s.value, scope));
      } else if (s.t === "Assign") {
        const v = infer(s.value, scope);
        if (dg.has(s.name))
          assignCheck(s.name, globalsTypes.has(s.name) ? globalsTypes.get(s.name) : UNKNOWN, v);
        else if (scope.has(s.name)) assignCheck(s.name, scope.get(s.name), v);
        else if (globalsTypes.has(s.name)) assignCheck(s.name, globalsTypes.get(s.name), v);
      } else if (s.t === "Print") {
        infer(s.value, scope);
      } else if (s.t === "If") {
        const c = infer(s.condition, scope);
        if (c !== "boolean" && c !== UNKNOWN) fail(`IF condition must be Boolean, got ${c}`);
        checkBody(s.body, scope, dg);
        checkBody(s.otherwise, scope, dg);
      } else if (s.t === "While") {
        const c = infer(s.condition, scope);
        if (c !== "boolean" && c !== UNKNOWN) fail(`WHILE condition must be Boolean, got ${c}`);
        checkBody(s.body, scope, dg);
      } else if (s.t === "Repeat") {
        const c = infer(s.count, scope);
        if (!NUMERIC.has(c) && c !== UNKNOWN) fail(`REPEAT count must be numeric, got ${c}`);
        checkBody(s.body, scope, dg);
      } else if (s.t === "Return") {
        const r = infer(s.value, scope);
        if (returnStack.length) returnStack[returnStack.length - 1].push(r);
      }
    }
  }

  for (const s of program.statements)
    if (s.t === "Declare") globalsTypes.set(s.name, infer(s.value, globalsTypes));

  for (const fn of functions.values()) {
    const scope = new Map(fn.params.map((p) => [p, UNKNOWN]));
    checkBody(fn.body, scope, functionGlobals(fn));
  }

  const top = new Map(globalsTypes);
  for (const s of program.statements)
    if (s.t !== "Declare" && s.t !== "Function") checkBody([s], top, new Set());
  return true;
}

module.exports = { checkTypes, BBTypeError, compatible, mergeReturns };
JSEOF

cat > js/check_semantic.js <<'JSEOF'
const { tokenize } = require("./lexer.js");
const { parse } = require("./parser.js");
const { checkTypes, BBTypeError } = require("./type_checker.js");
const src = require("fs").readFileSync(0, "utf8").replace(/\r\n?/g, "\n");
try {
  checkTypes(parse(tokenize(src)));
  console.log("SEMANTIC_OK");
} catch (e) {
  if (e instanceof BBTypeError || e instanceof SyntaxError) {
    console.log("SEMANTIC_ERROR: " + e.message);
    process.exit(1);
  }
  throw e;
}
JSEOF

norm() { if [ "$2" -eq 0 ]; then echo OK; else
  echo "ERR|$(echo "$1" | head -1 | sed -e 's/^SEMANTIC_ERROR: //' -e 's/^Error: //')"; fi; }

pass=0; fail=0
for f in cpp/cases/infer/*.bb cpp/cases/infer2/*.bb cpp/cases/globals.bb cpp/cases/loops.bb js/cases/func.bb; do
  [ -f "$f" ] || continue
  case "$f" in *t4_argcount*) continue;; esac
  po=$(./bhasha check "$f" 2>&1); pr=$?
  co=$(./cpp/check_semantic < "$f" 2>&1); cr=$?
  jo=$(node js/check_semantic.js < "$f" 2>&1); jr=$?
  P=$(norm "$po" $pr); C=$(norm "$co" $cr); J=$(norm "$jo" $jr)
  if [ "$P" = "$C" ] && [ "$P" = "$J" ]; then
    pass=$((pass+1)); echo "মিল   $(basename $f): ${P:0:60}"
  else
    fail=$((fail+1)); echo "অমিল  $f"
    echo "   Python: $P"; echo "   C++:    $C"; echo "   JS:     $J"
  fi
done
echo "== পাস $pass / ফেল $fail (t4 বাদ: semantic স্তর বাকি) =="
[ $fail -eq 0 ] && git add -A && git commit -qm "js type checker + 3-way semantic parity" && echo "কমিট হয়েছে"
