#pragma once
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <memory>
#include <set>
#include <utility>
#include "digit_zeros.hpp"
#include "lexer.hpp"

namespace bb {

// একটাই Node ধরন সব AST নোডের জন্য (Python-এর ast_nodes.py-র মতো একই ক্ষেত্র)
// body: Program-এর statements, Call-এর args, আর সব ব্লকের বডি
struct Node;
using NodeP = std::shared_ptr<Node>;
struct Node {
  std::string t, name, op, text;
  bool is_float = false, flag = false;
  double num = 0;
  NodeP a, b;
  std::vector<NodeP> body, otherwise;
  std::vector<std::pair<NodeP, NodeP>> pairs;
  std::vector<std::string> params;
  explicit Node(std::string type) : t(std::move(type)) {}
};
inline NodeP mk(const char* t) { return std::make_shared<Node>(t); }

inline std::string py_repr(const std::string& s) {
  char q = '\'';
  if (s.find('\'') != std::string::npos && s.find('"') == std::string::npos) q = '"';
  std::string out(1, q);
  for (unsigned char c : s) {
    if (c == '\\') out += "\\\\";
    else if (c == static_cast<unsigned char>(q)) { out += '\\'; out += q; }
    else if (c == '\n') out += "\\n";
    else if (c == '\r') out += "\\r";
    else if (c == '\t') out += "\\t";
    else if (c < 0x20 || c == 0x7f) {
      char b[8];
      std::snprintf(b, sizeof b, "\\x%02x", c);
      out += b;
    } else out += static_cast<char>(c);
  }
  out += q;
  return out;
}

inline int digit_value(char32_t c) {
  const char32_t* end = digits::ZEROS + digits::N;
  const char32_t* it = std::upper_bound(digits::ZEROS, end, c);
  return static_cast<int>(c - *(it - 1));
}

inline std::string to_ascii_digits(const std::string& s) {
  std::string out;
  for (size_t i = 0; i < s.size();) {
    char32_t cp;
    int len = decode(s, i, cp);
    if (cp == '.') out += '.';
    else out += static_cast<char>('0' + digit_value(cp));
    i += len;
  }
  return out;
}

// Python-এর repr(float)-এর নিয়ম
inline std::string py_float_repr(double v) {
  if (std::isinf(v)) return "inf";
  if (std::isnan(v)) return "nan";
  char buf[64];
  for (int prec = 0; prec < 17; prec++) {
    std::snprintf(buf, sizeof buf, "%.*e", prec, v);
    if (std::strtod(buf, nullptr) == v) break;
  }
  std::string s = buf;
  size_t e = s.find('e');
  std::string mant = s.substr(0, e), digits;
  int exp10 = std::atoi(s.c_str() + e + 1);
  for (char c : mant) if (c != '.') digits += c;
  while (digits.size() > 1 && digits.back() == '0') digits.pop_back();
  int nd = static_cast<int>(digits.size());
  int decpt = exp10 + 1;
  if (decpt <= -4 || decpt > 16) {
    std::string m(1, digits[0]);
    if (nd > 1) m += "." + digits.substr(1);
    int x = decpt - 1;
    char eb[16];
    std::snprintf(eb, sizeof eb, "e%c%02d", x < 0 ? '-' : '+', x < 0 ? -x : x);
    return m + eb;
  }
  if (decpt <= 0) return "0." + std::string(-decpt, '0') + digits;
  if (decpt >= nd) return digits + std::string(decpt - nd, '0') + ".0";
  return digits.substr(0, decpt) + "." + digits.substr(decpt);
}

inline void put_utf8(std::string& o, char32_t cp) {
  if (cp < 0x80) o += static_cast<char>(cp);
  else if (cp < 0x800) {
    o += static_cast<char>(0xC0 | (cp >> 6));
    o += static_cast<char>(0x80 | (cp & 0x3F));
  } else if (cp < 0x10000) {
    o += static_cast<char>(0xE0 | (cp >> 12));
    o += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
    o += static_cast<char>(0x80 | (cp & 0x3F));
  } else {
    o += static_cast<char>(0xF0 | (cp >> 18));
    o += static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
    o += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
    o += static_cast<char>(0x80 | (cp & 0x3F));
  }
}

inline char32_t hex_at(const std::string& b, size_t i, int n) {
  if (i + n > b.size()) throw SyntaxError("invalid escape in string literal");
  char32_t v = 0;
  for (int k = 0; k < n; k++) {
    char c = b[i + k];
    int d;
    if (c >= '0' && c <= '9') d = c - '0';
    else if (c >= 'a' && c <= 'f') d = c - 'a' + 10;
    else if (c >= 'A' && c <= 'F') d = c - 'A' + 10;
    else throw SyntaxError("invalid escape in string literal");
    v = v * 16 + d;
  }
  if (v > 0x10FFFF) throw SyntaxError("invalid escape in string literal");
  return v;
}

// Python-এর ast.literal_eval-এর মতো স্ট্রিং ব্যাখ্যা (সাধারণ escape গুলো)
inline std::string py_string_literal(const std::string& raw) {
  std::string body = raw.substr(1, raw.size() - 2), out;
  for (size_t i = 0; i < body.size(); i++) {
    char ch = body[i];
    if (ch == '\n') throw SyntaxError("unterminated string literal");
    if (ch != '\\') { out += ch; continue; }
    i++;
    char n = body[i];
    switch (n) {
      case '\\': out += '\\'; break;
      case '\'': out += '\''; break;
      case '"': out += '"'; break;
      case 'a': out += '\a'; break;
      case 'b': out += '\b'; break;
      case 'f': out += '\f'; break;
      case 'n': out += '\n'; break;
      case 'r': out += '\r'; break;
      case 't': out += '\t'; break;
      case 'v': out += '\v'; break;
      case 'x': put_utf8(out, hex_at(body, i + 1, 2)); i += 2; break;
      case 'u': put_utf8(out, hex_at(body, i + 1, 4)); i += 4; break;
      case 'U': put_utf8(out, hex_at(body, i + 1, 8)); i += 8; break;
      default:
        if (n >= '0' && n <= '7') {
          int v = n - '0', cnt = 1;
          while (cnt < 3 && i + 1 < body.size() && body[i + 1] >= '0' && body[i + 1] <= '7') {
            v = v * 8 + (body[++i] - '0');
            cnt++;
          }
          put_utf8(out, static_cast<char32_t>(v));
        } else {
          out += '\\';
          out += n;
        }
    }
  }
  return out;
}

inline int prec(const std::string& op) {
  if (op == "==" || op == "!=" || op == "<" || op == ">" || op == "<=" || op == ">=") return 1;
  if (op == "+" || op == "-") return 2;
  if (op == "*" || op == "/" || op == "%") return 3;
  return -1;
}

class Parser {
 public:
  explicit Parser(std::vector<Token> t) : toks_(std::move(t)) {}

  NodeP parse() {
    auto p = mk("Program");
    p->body = block({"EOF"});
    return p;
  }

 private:
  std::vector<Token> toks_;
  size_t pos_ = 0;
  int depth_ = 0;

  const Token& current() const { return toks_[pos_]; }

  Token advance() {
    Token t = toks_[pos_];
    if (t.kind != "EOF") pos_++;
    return t;
  }

  Token expect(const std::string& kind) {
    const Token& t = current();
    if (t.kind != kind)
      throw SyntaxError("Line " + std::to_string(t.line) + ": expected " + kind +
                        ", got " + py_repr(t.value));
    return advance();
  }

  void expect_op(const std::string& value) {
    Token t = expect("OP");
    if (t.value != value)
      throw SyntaxError("Line " + std::to_string(t.line) + ": expected " + py_repr(value));
  }

  bool is_op(const char* v) const {
    const Token& c = current();
    return c.kind == "OP" && c.value == v;
  }

  void newlines() {
    while (current().kind == "NEWLINE") advance();
  }

  void line_end() {
    const Token& t = current();
    if (t.kind != "NEWLINE" && t.kind != "EOF")
      throw SyntaxError("Line " + std::to_string(t.line) + ": unexpected " + py_repr(t.value));
    newlines();
  }

  std::vector<NodeP> block(std::initializer_list<const char*> stops) {
    std::vector<NodeP> out;
    newlines();
    auto stop = [&](const std::string& k) {
      for (auto s : stops) if (k == s) return true;
      return false;
    };
    while (!stop(current().kind)) {
      if (current().kind == "EOF") throw SyntaxError("Unexpected EOF: block is not closed");
      out.push_back(statement());
      line_end();
    }
    return out;
  }

  NodeP statement() {
    const std::string kind = current().kind;

    if (kind == "LET") {
      advance();
      std::string name = expect("IDENT").value;
      expect_op("=");
      auto n = mk("Declare");
      n->name = name;
      n->a = expression();
      return n;
    }
    if (kind == "PRINT") {
      advance();
      auto n = mk("Print");
      n->a = expression();
      return n;
    }
    if (kind == "BREAK") { advance(); return mk("Break"); }
    if (kind == "CONTINUE") { advance(); return mk("Continue"); }
    if (kind == "GLOBAL") {
      advance();
      auto n = mk("Global");
      n->name = expect("IDENT").value;
      return n;
    }
    if (kind == "RETURN") {
      advance();
      auto n = mk("Return");
      n->a = expression();
      return n;
    }
    if (kind == "IF") {
      advance();
      auto n = mk("If");
      n->a = expression();
      line_end();
      n->body = block({"ELSE", "END"});
      if (current().kind == "ELSE") {
        advance();
        line_end();
        n->otherwise = block({"END"});
      }
      expect("END");
      return n;
    }
    if (kind == "REPEAT" || kind == "WHILE") {
      advance();
      auto n = mk(kind == "REPEAT" ? "Repeat" : "While");
      n->a = expression();
      line_end();
      n->body = block({"END"});
      expect("END");
      return n;
    }
    if (kind == "FUNCTION") {
      advance();
      auto n = mk("Function");
      n->name = expect("IDENT").value;
      expect_op("(");
      if (!is_op(")")) {
        n->params.push_back(expect("IDENT").value);
        while (is_op(",")) {
          advance();
          n->params.push_back(expect("IDENT").value);
        }
      }
      expect_op(")");
      std::set<std::string> uniq(n->params.begin(), n->params.end());
      if (uniq.size() != n->params.size())
        throw SyntaxError("Duplicate parameter in " + n->name);
      line_end();
      n->body = block({"END"});
      expect("END");
      return n;
    }
    if (kind == "IDENT") {
      std::string name = advance().value;
      if (is_op("[")) {
        advance();
        auto index = expression();
        expect_op("]");
        expect_op("=");
        auto n = mk("IndexAssign");
        n->name = name;
        n->a = index;
        n->b = expression();
        return n;
      }
      auto n = mk("Assign");
      n->name = name;
      expect_op("=");
      n->a = expression();
      return n;
    }

    const Token& t = current();
    throw SyntaxError("Line " + std::to_string(t.line) + ": unknown statement " + py_repr(t.value));
  }

  NodeP expression(int minimum = 0) {
    if (++depth_ > 1000) throw SyntaxError("expression nested too deeply");
    struct Guard { int& d; ~Guard() { --d; } } guard{depth_};

    NodeP left = prefix();
    while (true) {
      
      if (is_op("[")) {
          advance();
          auto idx = expression();
          expect_op("]");
          auto call = mk("IndexRead");
          call->a = left;
          call->b = idx;
          left = call;
          continue;
      }
if (is_op("(")) {
        if (left->t != "Variable") break;
        advance();
        auto call = mk("Call");
        call->name = left->name;
        if (!is_op(")")) {
          call->body.push_back(expression());
          while (is_op(",")) {
            advance();
            call->body.push_back(expression());
          }
        }
        expect_op(")");
        left = call;
        continue;
      }
      if (current().kind != "OP") break;
      std::string op = current().value;
      int level = prec(op);
      if (level < minimum) break;
      advance();
      NodeP right = expression(level + 1);
      auto bin = mk("Binary");
      bin->a = left;
      bin->op = op;
      bin->b = right;
      left = bin;
    }
    return left;
  }

  NodeP prefix() {
    Token t = advance();

    if (t.kind == "NUMBER") {
      auto n = mk("Number");
      std::string ascii = to_ascii_digits(t.value);
      n->is_float = ascii.find('.') != std::string::npos;
      n->num = std::strtod(ascii.c_str(), nullptr);
      if (n->is_float) {
        n->text = py_float_repr(n->num);
        if (n->text.size() > 2 && n->text.compare(n->text.size() - 2, 2, ".0") == 0)
          n->text.erase(n->text.size() - 2);
      } else {
        size_t k = ascii.find_first_not_of('0');
        n->text = (k == std::string::npos) ? "0" : ascii.substr(k);
      }
      return n;
    }
    if (t.kind == "STRING") {
      auto n = mk("String");
      n->text = py_string_literal(t.value);
      return n;
    }
    if (t.kind == "TRUE" || t.kind == "FALSE") {
      auto n = mk("Boolean");
      n->flag = (t.kind == "TRUE");
      return n;
    }
    if (t.kind == "IDENT") {
      auto n = mk("Variable");
      n->name = t.value;
      return n;
    }
    if (t.kind == "OP" && t.value == "[") {
        auto n = mk("List");
        if (!is_op("]")) {
            n->body.push_back(expression());
            while (is_op(",")) {
                advance();
                n->body.push_back(expression());
            }
        }
        expect_op("]");
        return n;
    }
    if (t.kind == "OP" && t.value == "{") {
        auto n = mk("Dict");
        if (!is_op("}")) {
            auto key = expression();
            expect_op(":");
            auto val = expression();
            n->pairs.push_back({key, val});
            while (is_op(",")) {
                advance();
                if (is_op("}")) break;
                auto k = expression();
                expect_op(":");
                auto v = expression();
                n->pairs.push_back({k, v});
            }
        }
        expect_op("}");
        return n;
    }
    if (t.kind == "OP" && (t.value == "-" || t.value == "+")) {
      auto n = mk("Unary");
      n->op = t.value;
      n->a = expression(4);
      return n;
    }
    if (t.kind == "OP" && t.value == "(") {
      NodeP v = expression();
      expect_op(")");
      return v;
    }
    throw SyntaxError("Line " + std::to_string(t.line) + ": invalid expression " + py_repr(t.value));
  }
};

inline NodeP parse(const std::vector<Token>& tokens) { return Parser(tokens).parse(); }

}  // namespace bb
