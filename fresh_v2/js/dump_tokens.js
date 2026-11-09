const { tokenize } = require("./lexer.js");
const src = require("fs").readFileSync(process.argv[2], "utf8").replace(/\r\n?/g, "\n");
let out;
try { out = tokenize(src).map((t) => [t.kind, t.value, t.line, t.column]); }
catch (e) { if (!(e instanceof SyntaxError)) throw e; out = { error: e.message }; }
console.log(JSON.stringify(out));
