import re
import sys
from pathlib import Path

patterns = {
    "Possible shell execution": r"\bos\.system\s*\(|\bsubprocess\.Popen\s*\(",
    "Possible unsafe evaluation": r"\beval\s*\(|\bexec\s*\(",
    "Possible hardcoded secret": r"(?i)(password|api_key|secret)\s*=\s*['\"][^'\"]+",
}

for filename in sys.argv[1:]:
    text = Path(filename).read_text(encoding="utf-8")
    print(f"\nScanning: {filename}")
    found = False
    for label, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            print(f"WARNING: {label} at position {match.start()}")
            found = True
    if not found:
        print("No matching patterns found.")
