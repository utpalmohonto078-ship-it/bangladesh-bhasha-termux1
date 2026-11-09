import unicodedata
zeros = [cp for cp in range(0x110000)
         if chr(cp).isdecimal() and unicodedata.decimal(chr(cp)) == 0]
lines = ["#pragma once",
         "// স্বয়ংক্রিয়ভাবে তৈরি: python cpp/gen_digits.py",
         "#include <stddef.h>",
         "namespace bb { namespace digits {",
         "inline constexpr char32_t ZEROS[] = {"]
for i in range(0, len(zeros), 8):
    lines.append("  " + ", ".join("0x%X" % z for z in zeros[i:i + 8]) + ",")
lines += ["};",
          "inline constexpr size_t N = sizeof(ZEROS) / sizeof(ZEROS[0]);",
          "}}"]
open("cpp/digit_zeros.hpp", "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("শূন্য-অঙ্ক:", len(zeros))
