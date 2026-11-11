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
      case "List":
        for (const item of n.items)
          expression(item, scope, inFn, initMode);
        break;
      case "Dict":
        for (const pair of n.pairs) {
          expression(pair.key, scope, inFn, initMode);
          expression(pair.value, scope, inFn, initMode);
        }
        break;
      case "IndexRead":
        expression(n.target, scope, inFn, initMode);
        expression(n.index, scope, inFn, initMode);
        break;
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
        case "IndexAssign":
          if (!scope.has(s.name) && !dg.has(s.name) &&
              (inFn || !topGlobals.has(s.name)))
            err(`Assignment to undeclared variable: ${s.name}`);
          expression(s.index, scope, inFn);
          expression(s.value, scope, inFn);
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
