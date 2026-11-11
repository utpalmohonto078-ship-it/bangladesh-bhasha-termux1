from pathlib import Path


def lint_source(source: str):
    issues = []
    lines = source.splitlines()
    blank_count = 0

    for number, line in enumerate(lines, 1):
        if line.rstrip(" \t") != line:
            issues.append((number, "শেষে অপ্রয়োজনীয় whitespace"))

        if "\t" in line:
            issues.append((number, "Tab ব্যবহার করা হয়েছে; spaces ব্যবহার করুন"))

        if not line.strip():
            blank_count += 1
            if blank_count > 2:
                issues.append((number, "অতিরিক্ত blank line"))
        else:
            blank_count = 0

    return issues


def lint_file(path: str) -> bool:
    source = Path(path).read_text(encoding="utf-8")
    issues = lint_source(source)

    if not issues:
        print("কোনো style সমস্যা পাওয়া যায়নি:", path)
        return True

    print("Linter রিপোর্ট:", path)
    for number, message in issues:
        print(f"লাইন {number}: {message}")

    print("মোট সমস্যা:", len(issues))
    return False
