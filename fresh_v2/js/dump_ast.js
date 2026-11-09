const { tokenize } = require("./lexer.js");
const { parse } = require("./parser.js");
const src = require("fs").readFileSync(process.argv[2], "utf8").replace(/\r\n?/g, "\n");
function conv(n) {
  if (Array.isArray(n)) return n.map(conv);
  if (n && typeof n === "object") {
    if (n.t === "Number") return { t: "Number", value: n.isFloat ? { float: String(n.value) } : n.value };
    const o = {};
    for (const k of Object.keys(n)) o[k] = conv(n[k]);
    return o;
  }
  return n;
}
let out;
try { out = conv(parse(tokenize(src))); }
catch (e) { if (!(e instanceof SyntaxError)) throw e; out = { error: e.message }; }
console.log(JSON.stringify(out));
