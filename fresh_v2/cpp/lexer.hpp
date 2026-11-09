#pragma once
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include "unicode_tables.hpp"

namespace bb {

struct Token {
  std::string kind;
  std::string value;
  int line;
  int column;
};

struct SyntaxError : std::runtime_error {
  using std::runtime_error::runtime_error;
};

inline bool in(char32_t c, char32_t a, char32_t b) { return c >= a && c <= b; }

inline int decode(const std::string& s, size_t i, char32_t& cp) {
  unsigned char c = static_cast<unsigned char>(s[i]);
  if (c < 0x80) { cp = c; return 1; }
  int n = c >= 0xF0 ? 4 : c >= 0xE0 ? 3 : c >= 0xC0 ? 2 : 1;
  if (n == 1 || i + n > s.size()) { cp = 0xFFFD; return 1; }
  cp = c & (0xFF >> (n + 1));
  for (int k = 1; k < n; k++)
    cp = (cp << 6) | (static_cast<unsigned char>(s[i + k]) & 0x3F);
  return n;
}

inline int codepoints(const std::string& s) {
  int n = 0;
  for (unsigned char c : s) if ((c & 0xC0) != 0x80) n++;
  return n;
}

inline bool is_digit(char32_t c) { return uni::is_decimal(c); }

inline bool bengali_letter(char32_t c) {
  return c == 0x0980 || in(c, 0x0985, 0x098C) || in(c, 0x098F, 0x0990) ||
         in(c, 0x0993, 0x09A8) || in(c, 0x09AA, 0x09B0) || c == 0x09B2 ||
         in(c, 0x09B6, 0x09B9) || c == 0x09BD || c == 0x09CE ||
         in(c, 0x09DC, 0x09DD) || in(c, 0x09DF, 0x09E1) ||
         in(c, 0x09F0, 0x09F1) || in(c, 0x09F4, 0x09F9) || c == 0x09FC;
}

// অন্য ভাষার অক্ষর: আনুমানিক তালিকা (Latin, Greek, Cyrillic, Hebrew, Arabic/Persian,
// Hiragana, Katakana, CJK, Hangul)
inline bool other_letter(char32_t c) {
  return c == 0xAA || c == 0xB5 || c == 0xBA || in(c, 0xC0, 0xD6) ||
         in(c, 0xD8, 0xF6) || in(c, 0xF8, 0x2AF) || c == 0x386 ||
         in(c, 0x388, 0x3FF) || in(c, 0x400, 0x481) || in(c, 0x48A, 0x52F) ||
         in(c, 0x5D0, 0x5EA) || in(c, 0x620, 0x64A) || in(c, 0x66E, 0x6D3) ||
         in(c, 0x6FA, 0x6FC) || in(c, 0x1100, 0x11FF) || in(c, 0x3041, 0x3096) ||
         in(c, 0x309D, 0x309F) || in(c, 0x30A1, 0x30FA) || in(c, 0x30FC, 0x30FF) ||
         in(c, 0x3400, 0x4DBF) || in(c, 0x4E00, 0x9FFF) || in(c, 0xAC00, 0xD7A3) ||
         in(c, 0xF900, 0xFAFF) || in(c, 0xFF21, 0xFF3A) || in(c, 0xFF41, 0xFF5A) ||
         in(c, 0xFF66, 0xFF9D);
}

inline bool is_letter_start(char32_t c) { return uni::is_start(c); }

inline bool is_word(char32_t c) { return uni::is_word(c); }

inline size_t digits_end(const std::string& s, size_t p) {
  while (p < s.size()) {
    char32_t cp;
    int len = decode(s, p, cp);
    if (!is_digit(cp)) break;
    p += len;
  }
  return p;
}

inline std::string repr_char(const std::string& s, size_t pos, int len, char32_t cp) {
  if (cp == '\'') return "\"'\"";
  if (cp == '\\') return "'\\\\'";
  if (cp == '\r') return "'\\r'";
  if (cp < 0x20 || cp == 0x7f) {
    char buf[16];
    std::snprintf(buf, sizeof buf, "'\\x%02x'", static_cast<unsigned>(cp));
    return buf;
  }
  return "'" + s.substr(pos, len) + "'";
}

inline std::vector<Token> tokenize(std::string src) {
    // Normalize CRLF and lone CR into LF.
    std::string normalized;
    normalized.reserve(src.size());
    for (size_t i = 0; i < src.size(); ++i) {
        if (src[i] == '\r') {
            normalized += '\n';
            if (i + 1 < src.size() && src[i + 1] == '\n') ++i;
        } else {
            normalized += src[i];
        }
    }
    src.swap(normalized);
  static const std::unordered_map<std::string, std::string> KW = {
    {"সংখ্যা", "LET"}, {"let", "LET"}, {"var", "LET"},
    {"দেখাও", "PRINT"}, {"print", "PRINT"},
    {"সত্য", "TRUE"}, {"true", "TRUE"},
    {"মিথ্যা", "FALSE"}, {"false", "FALSE"},
    {"যদি", "IF"}, {"if", "IF"},
    {"নাহলে", "ELSE"}, {"else", "ELSE"},
    {"শেষ", "END"}, {"end", "END"},
    {"পুনরাবৃত্তি", "REPEAT"}, {"repeat", "REPEAT"},
    {"ফাংশন", "FUNCTION"}, {"function", "FUNCTION"},
    {"ফেরত", "RETURN"}, {"return", "RETURN"},
    {"গ্লোবাল", "GLOBAL"}, {"global", "GLOBAL"},
    {"যতক্ষণ", "WHILE"}, {"while", "WHILE"},
    {"থামো", "BREAK"}, {"break", "BREAK"},
    {"চালিয়ে_যাও", "CONTINUE"}, {"continue", "CONTINUE"},
  };

  std::vector<Token> toks;
  int line = 1, column = 1;
  size_t pos = 0;
  const size_t n = src.size();

  while (pos < n) {
    char32_t cp;
    int len = decode(src, pos, cp);
    size_t end = 0;
    std::string kind;

    if (cp == ' ' || cp == '\t') {
      end = pos;
      while (end < n && (src[end] == ' ' || src[end] == '\t')) end++;
      kind = "SPACE";
    } else if (is_digit(cp)) {
      end = digits_end(src, pos);
      if (end < n && src[end] == '.') {
        size_t e2 = digits_end(src, end + 1);
        if (e2 > end + 1) end = e2;
      }
      kind = "NUMBER";
    } else if (cp == '"' || cp == '\'') {
      size_t p = pos + 1;
      bool closed = false;
      while (p < n) {
        char c = src[p];
        if (c == '\\') {
          if (p + 1 >= n || src[p + 1] == '\n') break;
          char32_t ecp;
          int elen = decode(src, p + 1, ecp);
          p += 1 + elen;
        } else if (c == static_cast<char>(cp)) {
          p++;
          closed = true;
          break;
        } else {
          p++;
        }
      }
      if (closed) { end = p; kind = "STRING"; }
    } else if (is_letter_start(cp)) {
      end = pos + len;
      while (end < n) {
        char32_t c2;
        int l2 = decode(src, end, c2);
        if (!is_word(c2)) break;
        end += l2;
      }
      kind = "IDENT";
    } else if (cp == '\n') {
      end = pos + 1;
      kind = "NEWLINE";
    } else if (cp == '#') {
      end = pos;
      while (end < n && src[end] != '\n') end++;
      kind = "COMMENT";
    } else if (pos + 1 < n && src[pos + 1] == '=' &&
               (cp == '=' || cp == '!' || cp == '<' || cp == '>')) {
      end = pos + 2;
      kind = "OP";
    } else if (cp != 0 && cp < 0x80 && std::strchr("+-*/%=<>(),", static_cast<int>(cp))) {
      end = pos + 1;
      kind = "OP";
    }

    if (kind.empty()) {
      throw SyntaxError("Line " + std::to_string(line) + ", column " +
                        std::to_string(column) + ": invalid character " +
                        repr_char(src, pos, len, cp));
    }

    std::string value = src.substr(pos, end - pos);
    if (kind == "NEWLINE") {
      toks.push_back({"NEWLINE", value, line, column});
      line += 1;
      column = 1;
    } else {
      if (kind != "SPACE" && kind != "COMMENT") {
        if (kind == "IDENT") {
          auto it = KW.find(value);
          if (it != KW.end()) kind = it->second;
        }
        toks.push_back({kind, value, line, column});
      }
      column += codepoints(value);
    }
    pos = end;
  }
  toks.push_back({"EOF", "", line, column});
  return toks;
}

}  // namespace bb
