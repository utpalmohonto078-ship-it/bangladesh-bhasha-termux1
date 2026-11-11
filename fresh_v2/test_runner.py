import importlib.util
import subprocess
import sys


def run_tests(target="tests"):
    if importlib.util.find_spec("pytest") is None:
        print("pytest ইনস্টল করা নেই। ইনস্টল করুন:")
        print("python3 -m pip install pytest")
        return False

    command = [sys.executable, "-m", "pytest", "-q", target]
    result = subprocess.run(command, check=False)

    return result.returncode == 0
