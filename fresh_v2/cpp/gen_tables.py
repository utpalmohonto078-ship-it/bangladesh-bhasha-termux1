def runs(pred):
    out, lo = [], None
    for cp in range(0x110000):
        ok = pred(chr(cp))
        if ok and lo is None:
            lo = cp
        elif not ok and lo is not None:
            out.append((lo, cp - 1))
            lo = None
    if lo is not None:
        out.append((lo, 0x10FFFF))
    return out

def word(c):
    return c.isalnum() or c == "_"

tables = {
    "START": runs(lambda c: word(c) and not c.isdecimal()),
    "CONT": runs(lambda c: word(c) or "\u0980" <= c <= "\u09ff"),
    "DECIMAL": runs(lambda c: c.isdecimal()),
}

lines = [
    "#pragma once",
    "// স্বয়ংক্রিয়ভাবে তৈরি: python cpp/gen_tables.py",
    "#include <stddef.h>",
    "namespace bb { namespace uni {",
    "struct R { char32_t lo, hi; };",
]
for name, rs in tables.items():
    lines.append("inline constexpr R %s[] = {" % name)
    for i in range(0, len(rs), 6):
        lines.append("  " + ", ".join("{0x%X,0x%X}" % r for r in rs[i:i + 6]) + ",")
    lines.append("};")
lines += [
    "template <size_t N>",
    "inline bool in_table(const R (&t)[N], char32_t c) {",
    "  size_t lo = 0, hi = N;",
    "  while (lo < hi) {",
    "    size_t mid = (lo + hi) / 2;",
    "    if (c < t[mid].lo) hi = mid;",
    "    else if (c > t[mid].hi) lo = mid + 1;",
    "    else return true;",
    "  }",
    "  return false;",
    "}",
    "inline bool is_start(char32_t c) { return in_table(START, c); }",
    "inline bool is_word(char32_t c) { return in_table(CONT, c); }",
    "inline bool is_decimal(char32_t c) { return in_table(DECIMAL, c); }",
    "}}  // namespace bb::uni",
]
open("cpp/unicode_tables.hpp", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("তৈরি:", {k: len(v) for k, v in tables.items()})
