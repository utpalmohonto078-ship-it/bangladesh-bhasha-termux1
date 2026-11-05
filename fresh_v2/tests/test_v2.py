import unittest
from bb import compile_source, run_source

class FreshV2Tests(unittest.TestCase):
    def test_bengali(self):
        self.assertEqual(run_source(
            "সংখ্যা x = 10\nদেখাও x + 5\n"
        ), [15])

    def test_english(self):
        self.assertEqual(run_source(
            "let x = 8\nprint x * 3\n"
        ), [24])

    def test_precedence(self):
        self.assertEqual(run_source("দেখাও 2 + 3 * 4\n"), [14])

    def test_boolean(self):
        self.assertEqual(run_source("দেখাও সত্য == সত্য\n"), [True])

    def test_undefined_variable(self):
        with self.assertRaises(NameError):
            compile_source("দেখাও unknown\n")

    def test_duplicate_variable(self):
        with self.assertRaises(NameError):
            compile_source("সংখ্যা x = 1\nসংখ্যা x = 2\n")

    def test_if_else(self):
        src = (
            "সংখ্যা x = 8\n"
            "যদি x > 5\n"
            "দেখাও 1\n"
            "নাহলে\n"
            "দেখাও 0\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [1])

    def test_repeat(self):
        src = (
            "পুনরাবৃত্তি 3\n"
            "দেখাও 7\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [7, 7, 7])

    def test_nested_repeat(self):
        src = (
            "পুনরাবৃত্তি 2\n"
            "পুনরাবৃত্তি 2\n"
            "দেখাও 1\n"
            "শেষ\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [1, 1, 1, 1])

    def test_function(self):
        src = (
            "ফাংশন যোগ(a, b)\n"
            "ফেরত a + b\n"
            "শেষ\n"
            "দেখাও যোগ(10, 5)\n"
        )
        self.assertEqual(run_source(src), [15])

    def test_recursion(self):
        src = (
            "ফাংশন fact(n)\n"
            "যদি n <= 1\n"
            "ফেরত 1\n"
            "শেষ\n"
            "ফেরত n * fact(n - 1)\n"
            "শেষ\n"
            "দেখাও fact(5)\n"
        )
        self.assertEqual(run_source(src), [120])

    def test_global_write(self):
        src = (
            "সংখ্যা total = 10\n"
            "ফাংশন change()\n"
            "গ্লোবাল total\n"
            "total = total + 5\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
            "দেখাও total\n"
        )
        self.assertEqual(run_source(src), [15, 15])

    def test_global_inside_nested_block(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "যদি সত্য\n"
            "গ্লোবাল total\n"
            "শেষ\n"
            "total = total * 3\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
        )
        self.assertEqual(run_source(src), [6])

    def test_global_outside_function(self):
        with self.assertRaises(SyntaxError):
            compile_source("গ্লোবাল x\n")

    def test_global_parameter_conflict(self):
        src = (
            "সংখ্যা x = 1\n"
            "ফাংশন f(x)\n"
            "গ্লোবাল x\n"
            "ফেরত x\n"
            "শেষ\n"
        )
        with self.assertRaises(SyntaxError):
            compile_source(src)

    def test_function_argument_count(self):
        src = (
            "ফাংশন f(a)\n"
            "ফেরত a\n"
            "শেষ\n"
            "দেখাও f()\n"
        )
        with self.assertRaises(TypeError):
            compile_source(src)

    def test_return_outside_function(self):
        with self.assertRaises(SyntaxError):
            compile_source("ফেরত 5\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
