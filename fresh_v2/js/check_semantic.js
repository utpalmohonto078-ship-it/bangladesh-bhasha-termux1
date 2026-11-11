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
