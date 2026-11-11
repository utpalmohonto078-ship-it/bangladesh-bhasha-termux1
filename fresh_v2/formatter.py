from pathlib import Path


def format_source(source: str) -> str:
    """Safely normalize line endings without changing program content."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    if source and not source.endswith("\n"):
        source += "\n"
    return source


def format_file(path: str, check: bool = False) -> bool:
    file_path = Path(path)
    original = file_path.read_text(encoding="utf-8")
    formatted = format_source(original)

    if original == formatted:
        print("ইতিমধ্যে ফরম্যাট ঠিক আছে:", path)
        return True

    if check:
        print("ফরম্যাটিং প্রয়োজন:", path)
        return False

    file_path.write_text(formatted, encoding="utf-8", newline="")
    print("ফরম্যাট সম্পন্ন:", path)
    return True
