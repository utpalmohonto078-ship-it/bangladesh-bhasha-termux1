"use strict";

function pyRepr(s) {
  let q = "'";
  if (s.includes("'") && !s.includes('"')) q = '"';
  let out = "";
  for (const ch of s) {
    const c = ch.codePointAt(0);
    if (ch === "\\") out += "\\\\";
    else if (ch === q) out += "\\" + q;
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (c < 0x20 || c === 0x7f) out += "\\x" + c.toString(16).padStart(2, "0");
    else out += ch;
  }
  return q + out + q;
}

function toAsciiDigits(s) {
  let out = "";
  for (const ch of s) {
    const c = ch.codePointAt(0);
    out += c >= 0x09e6 && c <= 0x09ef ? String(c - 0x09e6) : ch;
  }
  return out;
}

function hexCode(body, i, n) {
  const h = body.slice(i, i + n);
  if (h.length !== n || !/^[0-9a-fA-F]+$/.test(h)) throw new SyntaxError("invalid escape in string literal");
  return h;
}

// Python-এর ast.literal_eval-এর মতো স্ট্রিং ব্যাখ্যা (সাধারণ escape গুলো)
function pyStringLiteral(raw) {
  const body = raw.slice(1, -1);
  let out = "";
  for (let i = 0; i < body.length; i++) {
    const ch = body[i];
    if (ch === "\n") throw new SyntaxError("unterminated string literal");
    if (ch !== "\\") { out += ch; continue; }
    i++;
    const n = body[i];
    if (n === "\\") out += "\\";
    else if (n === "'") out += "'";
    else if (n === '"') out += '"';
    else if (n === "a") out += "\x07";
    else if (n === "b") out += "\b";
    else if (n === "f") out += "\f";
    else if (n === "n") out += "\n";
    else if (n === "r") out += "\r";
    else if (n === "t") out += "\t";
    else if (n === "v") out += "\v";
    else if (n === "x") { out += String.fromCodePoint(parseInt(hexCode(body, i + 1, 2), 16)); i += 2; }
    else if (n === "u") { out += String.fromCodePoint(parseInt(hexCode(body, i + 1, 4), 16)); i += 4; }
    else if (n === "U") { out += String.fromCodePoint(parseInt(hexCode(body, i + 1, 8), 16)); i += 8; }
    else if (/[0-7]/.test(n)) {
      let oct = n;
      while (oct.length < 3 && /[0-7]/.test(body[i + 1] || "")) { i++; oct += body[i]; }
      out += String.fromCodePoint(parseInt(oct, 8));
    } else out += "\\" + n;
  }
  return out;
}

const PRECEDENCE = {
  "==": 1, "!=": 1, "<": 1, ">": 1, "<=": 1, ">=": 1,
  "+": 2, "-": 2, "*": 3, "/": 3, "%": 3,
};

class Parser {
  constructor(tokens) { this.tokens = tokens; this.pos = 0; }

  current() { return this.tokens[this.pos]; }

  advance() {
    const t = this.current();
    if (t.kind !== "EOF") this.pos += 1;
    return t;
  }

  expect(kind) {
    const t = this.current();
    if (t.kind !== kind) {
      throw new SyntaxError("Line " + t.line + ": expected " + kind + ", got " + pyRepr(t.value));
    }
    return this.advance();
  }

  expectOp(value) {
    const t = this.expect("OP");
    if (t.value !== value) {
      throw new SyntaxError("Line " + t.line + ": expected " + pyRepr(value));
    }
  }

  isOp(value) {
    const c = this.current();
    return c.kind === "OP" && c.value === value;
  }

  newlines() { while (this.current().kind === "NEWLINE") this.advance(); }

  lineEnd() {
    const t = this.current();
    if (t.kind !== "NEWLINE" && t.kind !== "EOF") {
      throw new SyntaxError("Line " + t.line + ": unexpected " + pyRepr(t.value));
    }
    this.newlines();
  }

  block(stops) {
    const statements = [];
    this.newlines();
    while (!stops.has(this.current().kind)) {
      if (this.current().kind === "EOF") throw new SyntaxError("Unexpected EOF: block is not closed");
      statements.push(this.statement());
      this.lineEnd();
    }
    return statements;
  }

  parse() {
    return { t: "Program", statements: this.block(new Set(["EOF"])) };
  }

  statement() {
    const kind = this.current().kind;

    if (kind === "LET") {
      this.advance();
      const name = this.expect("IDENT").value;
      this.expectOp("=");
      return { t: "Declare", name, value: this.expression() };
    }
    if (kind === "PRINT") { this.advance(); return { t: "Print", value: this.expression() }; }
    if (kind === "BREAK") { this.advance(); return { t: "Break" }; }
    if (kind === "CONTINUE") { this.advance(); return { t: "Continue" }; }
    if (kind === "GLOBAL") { this.advance(); return { t: "Global", name: this.expect("IDENT").value }; }
    if (kind === "RETURN") { this.advance(); return { t: "Return", value: this.expression() }; }

    if (kind === "IF") {
      this.advance();
      const condition = this.expression();
      this.lineEnd();
      const body = this.block(new Set(["ELSE", "END"]));
      let otherwise = [];
      if (this.current().kind === "ELSE") {
        this.advance();
        this.lineEnd();
        otherwise = this.block(new Set(["END"]));
      }
      this.expect("END");
      return { t: "If", condition, body, otherwise };
    }

    if (kind === "REPEAT") {
      this.advance();
      const count = this.expression();
      this.lineEnd();
      const body = this.block(new Set(["END"]));
      this.expect("END");
      return { t: "Repeat", count, body };
    }

    if (kind === "WHILE") {
      this.advance();
      const condition = this.expression();
      this.lineEnd();
      const body = this.block(new Set(["END"]));
      this.expect("END");
      return { t: "While", condition, body };
    }

    if (kind === "FUNCTION") {
      this.advance();
      const name = this.expect("IDENT").value;
      this.expectOp("(");
      const params = [];
      if (!this.isOp(")")) {
        params.push(this.expect("IDENT").value);
        while (this.isOp(",")) {
          this.advance();
          params.push(this.expect("IDENT").value);
        }
      }
      this.expectOp(")");
      if (params.length !== new Set(params).size) {
        throw new SyntaxError("Duplicate parameter in " + name);
      }
      this.lineEnd();
      const body = this.block(new Set(["END"]));
      this.expect("END");
      return { t: "Function", name, params, body };
    }

    if (kind === "IDENT") {
      const name = this.advance().value;
      if (this.isOp("[")) {
        this.advance();
        const index = this.expression();
        this.expectOp("]");
        this.expectOp("=");
        return { t: "IndexAssign", name, index, value: this.expression() };
      }
      this.expectOp("=");
      return { t: "Assign", name, value: this.expression() };
    }

    const t = this.current();
    throw new SyntaxError("Line " + t.line + ": unknown statement " + pyRepr(t.value));
  }

  expression(minimum = 0) {
    let left = this.prefix();

    while (true) {
      
      if (this.isOp("[")) {
        this.advance();
        const index = this.expression();
        this.expectOp("]");
        left = { t: "IndexRead", target: left, index };
        continue;
      }
if (this.isOp("(")) {
        if (left.t !== "Variable") break;
        this.advance();
        const args = [];
        if (!this.isOp(")")) {
          args.push(this.expression());
          while (this.isOp(",")) {
            this.advance();
            args.push(this.expression());
          }
        }
        this.expectOp(")");
        left = { t: "Call", name: left.name, args };
        continue;
      }

      if (this.current().kind !== "OP") break;

      const op = this.current().value;
      const level = Object.prototype.hasOwnProperty.call(PRECEDENCE, op) ? PRECEDENCE[op] : -1;
      if (level < minimum) break;

      this.advance();
      const right = this.expression(level + 1);
      left = { t: "Binary", left, operator: op, right };
    }
    return left;
  }

  prefix() {
    const token = this.advance();

    if (token.kind === "NUMBER") {
      const isFloat = token.value.includes(".");
      return { t: "Number", value: Number(toAsciiDigits(token.value)), isFloat };
    }
    if (token.kind === "STRING") return { t: "String", value: pyStringLiteral(token.value) };
    if (token.kind === "TRUE") return { t: "Boolean", value: true };
    if (token.kind === "FALSE") return { t: "Boolean", value: false };
    if (token.kind === "IDENT") return { t: "Variable", name: token.value };
    if (token.kind === "OP" && token.value === "[") {
      const items = [];
      if (!this.isOp("]")) {
        items.push(this.expression());
        while (this.isOp(",")) {
          this.advance();
          items.push(this.expression());
        }
      }
      this.expectOp("]");
      return { t: "List", items };
    }
    if (token.kind === "OP" && token.value === "{") {
      const pairs = [];
      if (!this.isOp("}")) {
        const key = this.expression();
        this.expectOp(":");
        const val = this.expression();
        pairs.push({ key, value: val });
        while (this.isOp(",")) {
          this.advance();
          if (this.isOp("}")) break;
          const k = this.expression();
          this.expectOp(":");
          const v = this.expression();
          pairs.push({ key: k, value: v });
        }
      }
      this.expectOp("}");
      return { t: "Dict", pairs };
    }

    if (token.kind === "OP" && (token.value === "-" || token.value === "+")) {
      return { t: "Unary", operator: token.value, operand: this.expression(4) };
    }
    if (token.kind === "OP" && token.value === "(") {
      const value = this.expression();
      this.expectOp(")");
      return value;
    }

    throw new SyntaxError("Line " + token.line + ": invalid expression " + pyRepr(token.value));
  }
}

function parse(tokens) { return new Parser(tokens).parse(); }

module.exports = { parse, Parser, pyRepr };
