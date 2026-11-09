#include <cstdio>
#include <fstream>
#include <iostream>
#include <sstream>
#include "lexer.hpp"

static std::string normalize(const std::string& s) {
  std::string o;
  o.reserve(s.size());
  for (size_t i = 0; i < s.size(); i++) {
    if (s[i] == '\r') {
      o += '\n';
      if (i + 1 < s.size() && s[i + 1] == '\n') i++;
    } else {
      o += s[i];
    }
  }
  return o;
}

static std::string json_str(const std::string& s) {
  std::string o = "\"";
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
  return o + "\"";
}

int main(int argc, char** argv) {
  if (argc != 2) { std::cerr << "usage: dump_tokens FILE\n"; return 2; }
  std::ifstream f(argv[1], std::ios::binary);
  if (!f) { std::cerr << "cannot open " << argv[1] << "\n"; return 1; }
  std::stringstream ss;
  ss << f.rdbuf();
  std::string src = normalize(ss.str());
  try {
    auto toks = bb::tokenize(src);
    std::string out = "[";
    for (size_t i = 0; i < toks.size(); i++) {
      if (i) out += ",";
      out += "[" + json_str(toks[i].kind) + "," + json_str(toks[i].value) + "," +
             std::to_string(toks[i].line) + "," + std::to_string(toks[i].column) + "]";
    }
    out += "]";
    std::cout << out << "\n";
  } catch (const bb::SyntaxError& e) {
    std::cout << "{\"error\":" << json_str(e.what()) << "}\n";
  }
  return 0;
}
