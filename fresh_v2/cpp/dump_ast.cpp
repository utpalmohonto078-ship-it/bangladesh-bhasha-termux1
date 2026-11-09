#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include "parser.hpp"

static std::string normalize(const std::string& s) {
  std::string o;
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '\r') {
      o += '\n';
      if (i + 1 < s.size() && s[i + 1] == '\n') i++;
    } else o += s[i];
  }
  return o;
}

static void jstr(std::string& o, const std::string& s) {
  o += '"';
  for (unsigned char c : s) {
    if (c == '"') o += "\\\"";
    else if (c == '\\') o += "\\\\";
    else if (c == '\n') o += "\\n";
    else if (c == '\r') o += "\\r";
    else if (c == '\t') o += "\\t";
    else if (c == '\b') o += "\\b";
    else if (c == '\f') o += "\\f";
    else if (c < 0x20) { char b[8]; std::snprintf(b, sizeof b, "\\u%04x", c); o += b; }
    else o += static_cast<char>(c);
  }
  o += '"';
}

static void dump(const bb::NodeP& n, std::string& o);

static void list(const std::vector<bb::NodeP>& v, std::string& o) {
  o += '[';
  for (size_t i = 0; i < v.size(); i++) {
    if (i) o += ',';
    dump(v[i], o);
  }
  o += ']';
}

static void dump(const bb::NodeP& n, std::string& o) {
  const std::string& t = n->t;
  o += "{\"t\":";
  jstr(o, t);
  auto key = [&](const char* k) { o += ",\""; o += k; o += "\":"; };
  if (t == "Program") { key("statements"); list(n->body, o); }
  else if (t == "Number") {
    key("value");
    if (n->is_float) { o += "{\"float\":"; jstr(o, n->text); o += "}"; }
    else o += n->text;
  }
  else if (t == "String") { key("value"); jstr(o, n->text); }
  else if (t == "Boolean") { key("value"); o += n->flag ? "true" : "false"; }
  else if (t == "Variable") { key("name"); jstr(o, n->name); }
  else if (t == "Binary") {
    key("left"); dump(n->a, o);
    key("operator"); jstr(o, n->op);
    key("right"); dump(n->b, o);
  }
  else if (t == "Unary") { key("operator"); jstr(o, n->op); key("operand"); dump(n->a, o); }
  else if (t == "Call") { key("name"); jstr(o, n->name); key("args"); list(n->body, o); }
  else if (t == "Declare" || t == "Assign") { key("name"); jstr(o, n->name); key("value"); dump(n->a, o); }
  else if (t == "Print" || t == "Return") { key("value"); dump(n->a, o); }
  else if (t == "If") {
    key("condition"); dump(n->a, o);
    key("body"); list(n->body, o);
    key("otherwise"); list(n->otherwise, o);
  }
  else if (t == "Repeat") { key("count"); dump(n->a, o); key("body"); list(n->body, o); }
  else if (t == "While") { key("condition"); dump(n->a, o); key("body"); list(n->body, o); }
  else if (t == "Function") {
    key("name"); jstr(o, n->name);
    key("params");
    o += '[';
    for (size_t i = 0; i < n->params.size(); i++) {
      if (i) o += ',';
      jstr(o, n->params[i]);
    }
    o += ']';
    key("body"); list(n->body, o);
  }
  else if (t == "Global") { key("name"); jstr(o, n->name); }
  o += '}';
}

int main(int argc, char** argv) {
  if (argc != 2) { std::cerr << "usage: dump_ast FILE\n"; return 2; }
  std::ifstream f(argv[1], std::ios::binary);
  if (!f) { std::cerr << "cannot open " << argv[1] << "\n"; return 1; }
  std::stringstream ss;
  ss << f.rdbuf();
  std::string src = normalize(ss.str()), out;
  try {
    dump(bb::parse(bb::tokenize(src)), out);
  } catch (const bb::SyntaxError& e) {
    out = "{\"error\":";
    jstr(out, e.what());
    out += "}";
  }
  std::cout << out << "\n";
  return 0;
}
