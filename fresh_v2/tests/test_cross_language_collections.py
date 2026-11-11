import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    (
        "valid_collections",
        '''let xs = [10, 20]
xs[0] = 30
let d = {"a": 1}
d["a"] = 2
print xs[0]
print d["a"]
''',
        True,
        None,
    ),
    (
        "bad_list_read_index",
        '''let xs = [10, 20]
print xs["bad"]
''',
        False,
        "Index must be integer",
    ),
    (
        "bad_list_assignment_index",
        '''let xs = [10, 20]
xs["bad"] = 30
''',
        False,
        "Index must be integer",
    ),
    (
        "bad_dict_read_key",
        '''let d = {"a": 1}
print d[true]
''',
        False,
        "Dict key must be string or integer",
    ),
    (
        "bad_dict_assignment_key",
        '''let d = {"a": 1}
d[true] = 20
''',
        False,
        "Dict key must be string or integer",
    ),
    (
        "undeclared_index_assignment",
        '''missing[0] = 10
''',
        False,
        "undeclared",
    ),
]


class CrossLanguageCollectionTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        cls.gxx = shutil.which("g++")

        if not cls.node or not cls.gxx:
            raise unittest.SkipTest("Node.js অথবা g++ পাওয়া যায়নি")

        cls.tempdir = tempfile.TemporaryDirectory()
        cls.cpp_binary = str(Path(cls.tempdir.name) / "bb_cpp_semantic")

        build = subprocess.run(
            [
                cls.gxx,
                "-std=c++17",
                str(ROOT / "cpp" / "check_semantic.cpp"),
                "-o",
                cls.cpp_binary,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        if build.returncode != 0:
            raise RuntimeError("C++ build failed:\n" + build.stderr)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "tempdir"):
            cls.tempdir.cleanup()

    def run_checker(self, command, source):
        return subprocess.run(
            command,
            input=source,
            text=True,
            capture_output=True,
            cwd=ROOT,
        )

    def check_both(self, source, should_pass, expected_error):
        js = self.run_checker(
            [self.node, "js/check_semantic.js"], source
        )
        cpp = self.run_checker(
            [self.cpp_binary], source
        )

        self.assertEqual(
            js.returncode == 0,
            should_pass,
            "JavaScript result:\n" + js.stdout + js.stderr,
        )
        self.assertEqual(
            cpp.returncode == 0,
            should_pass,
            "C++ result:\n" + cpp.stdout + cpp.stderr,
        )

        if should_pass:
            self.assertIn("SEMANTIC_OK", js.stdout)
            self.assertIn("SEMANTIC_OK", cpp.stdout)
        else:
            self.assertIn(expected_error, js.stdout + js.stderr)
            self.assertIn(expected_error, cpp.stdout + cpp.stderr)

    def test_valid_collections(self):
        self.check_both(CASES[0][1], True, None)

    def test_bad_list_read_index(self):
        self.check_both(CASES[1][1], False, CASES[1][3])

    def test_bad_list_assignment_index(self):
        self.check_both(CASES[2][1], False, CASES[2][3])

    def test_bad_dict_read_key(self):
        self.check_both(CASES[3][1], False, CASES[3][3])

    def test_bad_dict_assignment_key(self):
        self.check_both(CASES[4][1], False, CASES[4][3])

    def test_undeclared_index_assignment(self):
        self.check_both(CASES[5][1], False, CASES[5][3])


if __name__ == "__main__":
    unittest.main()
