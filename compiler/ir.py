import json
import unicodedata
import re
import sys
from pathlib import Path

VERSION = "ULTIMATE-IR-1.0"

def compile_source(source):
    instructions = []

    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        match = re.fullmatch(
            r"(?:LET|সংখ্যা|লেখা|তালিকা)\s+([A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*)\s*=\s*(.+)", line
        )
        if match:
            instructions.append({
                "op": "LET",
                "name": unicodedata.normalize("NFKC", match.group(1)),
                "value": match.group(2),
                "line": number
            })
            continue

        match = re.fullmatch(r"(?:PRINT|দেখাও)\s+(.+)", line)
        if match:
            instructions.append({
                "op": "PRINT",
                "value": match.group(1),
                "line": number
            })
            continue

        if line.startswith(("IF ", "যদি ")):
            instructions.append({
                "op": "IF",
                "condition": line.split(maxsplit=1)[1],
                "line": number
            })
        elif line in ("ELSE", "নাহলে"):
            instructions.append({"op": "ELSE", "line": number})
        elif line in ("END", "শেষ"):
            instructions.append({"op": "END", "line": number})
        elif line.startswith(("REPEAT ", "পুনরাবৃত্তি ")):
            instructions.append({
                "op": "REPEAT",
                "count": line.split(maxsplit=1)[1],
                "line": number
            })
        elif line.startswith(("FUNCTION ", "ফাংশন ")):
            instructions.append({
                "op": "FUNCTION",
                "source": unicodedata.normalize("NFKC", line),
                "line": number
            })
        elif line.startswith(("RETURN ", "ফেরত ")):
            instructions.append({
                "op": "RETURN",
                "value": line.split(maxsplit=1)[1],
                "line": number
            })
        else:
            assign = re.fullmatch(
                r"([A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*)\s*=(?!=)\s*(.+)", line
            )
            call = re.fullmatch(r"[A-Za-z_\u0985-\u09B9\u09DC-\u09DF][\w\u09BC-\u09CD\u09D7\u0985-\u09B9\u09DC-\u09DF\u09E6-\u09EF]*\s*\(.*\)", line)
            if assign:
                instructions.append({
                    "op": "LET",
                    "name": unicodedata.normalize("NFKC", assign.group(1)),
                    "value": assign.group(2),
                    "line": number
                })
            elif call:
                instructions.append({
                    "op": "LET",
                    "name": "__discard__",
                    "value": line,
                    "line": number
                })
            else:
                raise ValueError(
                    f"Line {number}: Unknown command: {line}"
                )

    return {
        "language": "BANGLADESH BHASHA",
        "version": VERSION,
        "format": "BB-IR-1",
        "instructions": instructions
    }

def main():
    if len(sys.argv) != 2:
        print("Usage: python compiler/ir.py file.bb")
        return 2

    source_file = Path(sys.argv[1])

    if not source_file.is_file() or source_file.suffix != ".bb":
        print("ERROR: Valid .bb file required")
        return 1

    try:
        result = compile_source(
            source_file.read_text(encoding="utf-8")
        )

        output = Path("build") / (source_file.stem + ".ir.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print("PASS: Source parsed")
        print("PASS: IR generated:", output)
        print("Instructions:", len(result["instructions"]))
        return 0

    except (ValueError, OSError) as error:
        print("COMPILER ERROR:", error)
        return 1

if __name__ == "__main__":
    sys.exit(main())
