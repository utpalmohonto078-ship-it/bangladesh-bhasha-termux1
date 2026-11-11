"use strict";

const KEYWORDS = {
  "সংখ্যা": "LET", "let": "LET", "var": "LET",
  "দেখাও": "PRINT", "print": "PRINT",
  "সত্য": "TRUE", "true": "TRUE",
  "মিথ্যা": "FALSE", "false": "FALSE",
  "যদি": "IF", "if": "IF",
  "নাহলে": "ELSE", "else": "ELSE",
  "শেষ": "END", "end": "END",
  "পুনরাবৃত্তি": "REPEAT", "repeat": "REPEAT",
  "ফাংশন": "FUNCTION", "function": "FUNCTION",
  "ফেরত": "RETURN", "return": "RETURN",
  "গ্লোবাল": "GLOBAL", "global": "GLOBAL",
  "যতক্ষণ": "WHILE", "while": "WHILE",
  "থামো": "BREAK", "break": "BREAK",
  "চালিয়ে_যাও": "CONTINUE", "continue": "CONTINUE",
};

const W = "[\\p{L}\\p{N}_\u0980-\u09FF]";
const PATTERN = new RegExp(
  "(?<SPACE>[ \\t]+)|" +
  "(?<NUMBER>[0-9\u09E6-\u09EF]+(?:\\.[0-9\u09E6-\u09EF]+)?)|" +
  "(?<STRING>\"(?:\\\\.|[^\"\\\\])*\"|'(?:\\\\.|[^'\\\\])*')|" +
  "(?<IDENT>[\\p{L}_]" + W + "*)|" +
  "(?<OP>==|!=|<=|>=|[+\\-*/%=<>(),\\[\\]{}:])|" +
  "(?<NEWLINE>\\n)|" +
  "(?<COMMENT>#[^\\n]*)",
  "uy"
);

const KINDS = ["SPACE", "NUMBER", "STRING", "IDENT", "OP", "NEWLINE", "COMMENT"];

function tokenize(source) {
  const tokens = [];
  let line = 1, column = 1, pos = 0;

  while (pos < source.length) {
    PATTERN.lastIndex = pos;
    const m = PATTERN.exec(source);
    if (!m) {
      const ch = String.fromCodePoint(source.codePointAt(pos));
      const shown = ch === "'" ? '"\'"' : "'" + ch + "'";
      throw new SyntaxError(
        "Line " + line + ", column " + column + ": invalid character " + shown
      );
    }
    let kind = KINDS.find((k) => m.groups[k] !== undefined);
    const value = m[0];

    if (kind === "NEWLINE") {
      tokens.push({ kind: "NEWLINE", value, line, column });
      line += 1;
      column = 1;
    } else {
      if (kind !== "SPACE" && kind !== "COMMENT") {
        if (kind === "IDENT" && Object.prototype.hasOwnProperty.call(KEYWORDS, value)) {
          kind = KEYWORDS[value];
        }
        tokens.push({ kind, value, line, column });
      }
      column += [...value].length;
    }
    pos = PATTERN.lastIndex;
  }
  tokens.push({ kind: "EOF", value: "", line, column });
  return tokens;
}

module.exports = { tokenize, KEYWORDS };
