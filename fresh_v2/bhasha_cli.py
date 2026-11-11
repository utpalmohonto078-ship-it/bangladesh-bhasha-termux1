import sys
from pathlib import Path

from bb import compile_source, run_source
from formatter import format_file
from linter import lint_file
from validator import validate_file
from test_runner import run_tests
from debugger import debug_file
from package_manager import handle_package_command

VERSION = "2.0.1"

HELP = """BANGLADESH BHASHA — ULTIMATE

ব্যবহার:
  bhasha run <file.bb>      প্রোগ্রাম চালান
  bhasha <file.bb>          সংক্ষিপ্ত run
  bhasha check <file.bb>    প্রোগ্রাম পরীক্ষা
  bhasha format <file.bb>  ফরম্যাট করুন
  bhasha lint <file.bb>    Style পরীক্ষা
  bhasha validate <file.bb> Syntax ও compilation যাচাই
  bhasha test [path]        Test Suite চালান
  bhasha debug <file.bb>   Debug mode চালান
  bhasha format --check <file.bb> ফরম্যাট যাচাই
  bhasha pkg                Package Manager
  bhasha repl               ইন্টারেক্টিভ মোড
  bhasha version            সংস্করণ
  bhasha help               সাহায্য
"""

def read(path):
    return Path(path).read_text(encoding="utf-8")

def run_file(path):
    for result in run_source(read(path)) or []:
        print(result)

def check_file(path):
    compile_source(read(path))
    print("ঠিক আছে:", path)

def repl():
    print("BANGLADESH BHASHA REPL (exit লিখে বের হন)")
    while True:
        try:
            line = input("বাংলা-ভাষা> ")
        except (EOFError, KeyboardInterrupt):
            print("\nবিদায়!")
            break

        if line.strip().lower() in ("exit", "quit"):
            print("বিদায়!")
            break
        if not line.strip():
            continue

        try:
            for result in run_source(line + "\n") or []:
                print(result)
        except Exception as error:
            print("Error:", error)

def main():
    args = sys.argv[1:]
    try:
        if not args or args[0] == "repl":
            repl()
        elif args[0] in ("help", "-h", "--help"):
            print(HELP)
        elif args[0] in ("version", "--version"):
            print("BANGLADESH BHASHA", VERSION)
        elif args[0] == "pkg":
            if not handle_package_command(args[1:]):
                raise SystemExit(1)
        elif args[0] == "debug" and len(args) > 1:
            debug_file(args[1])
        elif args[0] == "test":
            target = args[1] if len(args) > 1 else "tests"
            if not run_tests(target):
                raise SystemExit(1)
        elif args[0] == "check" and len(args) > 1:
            check_file(args[1])
        elif args[0] == "validate" and len(args) > 1:
            if not validate_file(args[1]):
                raise SystemExit(1)
        elif args[0] == "lint" and len(args) > 1:
            if not lint_file(args[1]):
                raise SystemExit(1)
        elif args[0] == "format" and len(args) > 1:
            if args[1] == "--check" and len(args) > 2:
                if not format_file(args[2], check=True):
                    raise SystemExit(1)
            else:
                format_file(args[1])
        elif args[0] == "run" and len(args) > 1:
            run_file(args[1])
        elif len(args) == 1:
            run_file(args[0])
        else:
            print(HELP)
            raise SystemExit(2)
    except FileNotFoundError as error:
        print(f"ফাইল পাওয়া যায়নি: {error.filename}")
        raise SystemExit(1)
    except Exception as error:
        print(f"Error: {error}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
