from pathlib import Path
from bb import compile_source


def validate_source(source: str):
    try:
        compile_source(source)
        return []
    except Exception as error:
        return [str(error)]


def validate_file(path: str) -> bool:
    source = Path(path).read_text(encoding="utf-8")
    errors = validate_source(source)

    if not errors:
        print("Validation সফল:", path)
        return True

    print("Validation ব্যর্থ:", path)
    for error in errors:
        print("ত্রুটি:", error)
    return False
