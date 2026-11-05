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

    def test_global_inside_repeat(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "পুনরাবৃত্তি 2\n"
            "গ্লোবাল total\n"
            "শেষ\n"
            "total = total * 3\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
        )
        self.assertEqual(run_source(src), [6])

    def test_global_inside_else(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "যদি মিথ্যা\n"
            "দেখাও 0\n"
            "নাহলে\n"
            "গ্লোবাল total\n"
            "শেষ\n"
            "total = total * 3\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
            "দেখাও total\n"
        )
        self.assertEqual(run_source(src), [6, 6])

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

    def test_while(self):
        src = (
            "সংখ্যা i = 0\n"
            "যতক্ষণ i < 5\n"
            "দেখাও i\n"
            "i = i + 1\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [0, 1, 2, 3, 4])

    def test_global_inside_while(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "সংখ্যা i = 0\n"
            "যতক্ষণ i < 2\n"
            "গ্লোবাল total\n"
            "total = total + 1\n"
            "i = i + 1\n"
            "শেষ\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
            "দেখাও total\n"
        )
        self.assertEqual(run_source(src), [4, 4])

    def test_while_false_initially(self):
        src = (
            "সংখ্যা i = 0\n"
            "যতক্ষণ মিথ্যা\n"
            "i = i + 1\n"
            "দেখাও 99\n"
            "শেষ\n"
            "দেখাও i\n"
        )
        self.assertEqual(run_source(src), [0])

    def test_while(self):
        src = (
            "সংখ্যা i = 0\n"
            "যতক্ষণ i < 5\n"
            "দেখাও i\n"
            "i = i + 1\n"
            "শেষ\n"
        )
        self.assertEqual(run_source(src), [0, 1, 2, 3, 4])

    def test_global_inside_while(self):
        src = (
            "সংখ্যা total = 2\n"
            "ফাংশন change()\n"
            "সংখ্যা i = 0\n"
            "যতক্ষণ i < 2\n"
            "গ্লোবাল total\n"
            "total = total + 1\n"
            "i = i + 1\n"
            "শেষ\n"
            "ফেরত total\n"
            "শেষ\n"
            "দেখাও change()\n"
            "দেখাও total\n"
        )
        self.assertEqual(run_source(src), [4, 4])

    def test_while_false_initially(self):
        src = (
            "সংখ্যা i = 0\n"
            "যতক্ষণ মিথ্যা\n"
            "i = i + 1\n"
            "দেখাও 99\n"
            "শেষ\n"
            "দেখাও i\n"
        )
        self.assertEqual(run_source(src), [0])


    def test_advanced_while_english(self):
        src = (
            "let i = 0\n"
            "while i < 3\n"
            "print i\n"
            "i = i + 1\n"
            "end\n"
        )
        self.assertEqual(run_source(src), [0, 1, 2])

    def test_nested_while(self):
        src = (
            "let i = 0\n"
            "while i < 2\n"
            "let j = 0\n"
            "while j < 2\n"
            "print i * 10 + j\n"
            "j = j + 1\n"
            "end\n"
            "i = i + 1\n"
            "end\n"
        )
        self.assertEqual(run_source(src), [0, 1, 10, 11])

    def test_negative_numbers(self):
        self.assertEqual(run_source("দেখাও -5 + 3\n"), [-2])

    def test_multiple_variables(self):
        src = (
            "সংখ্যা a = 10\n"
            "সংখ্যা b = 20\n"
            "দেখাও a * b\n"
        )
        self.assertEqual(run_source(src), [200])

    def test_builtin_type_detection(self):
        src = (
            "সংখ্যা a = 34\n"
            "সংখ্যা b = 12.5\n"
            "সংখ্যা c = \"বাংলাদেশ\"\n"
            "সংখ্যা d = সত্য\n"
            "দেখাও ধরন(a)\n"
            "দেখাও ধরন(b)\n"
            "দেখাও ধরন(c)\n"
            "দেখাও ধরন(d)\n"
        )
        self.assertEqual(
            run_source(src),
            ["integer", "float", "string", "boolean"]
        )

    def test_builtin_length(self):
        self.assertEqual(
            run_source('দেখাও দৈর্ঘ্য("বাংলাদেশ")\n'),
            [8]
        )

    def test_builtin_english_aliases(self):
        self.assertEqual(
            run_source('let name = "Bangladesh"\nprint length(name)\nprint type_of(name)\n'),
            [10, "string"]
        )

    def test_builtin_argument_count(self):
        with self.assertRaises(TypeError):
            compile_source("দেখাও ধরন()\n")

    def test_builtin_length_rejects_non_string(self):
        with self.assertRaises(TypeError):
            run_source("দেখাও দৈর্ঘ্য(123)\n")

    def test_global_initializer_order(self):
        src = (
            "সংখ্যা a = b\n"
            "সংখ্যা b = 1\n"
            "দেখাও a\n"
        )
        with self.assertRaises(NameError):
            run_source(src)

    def test_while_break(self):
        src = 'let i = 0\nwhile i < 10\ni = i + 1\nif i == 4\nbreak\nend\nprint i\nend' + "\n"
        self.assertEqual(run_source(src), [1, 2, 3])

    def test_while_continue(self):
        src = 'let i = 0\nwhile i < 5\ni = i + 1\nif i == 3\ncontinue\nend\nprint i\nend' + "\n"
        self.assertEqual(run_source(src), [1, 2, 4, 5])

    def test_repeat_break(self):
        src = 'let n = 0\nrepeat 10\nn = n + 1\nif n == 3\nbreak\nend\nend\nprint n' + "\n"
        self.assertEqual(run_source(src), [3])

    def test_repeat_continue(self):
        src = 'let n = 0\nrepeat 5\nn = n + 1\nif n == 2\ncontinue\nend\nprint n\nend' + "\n"
        self.assertEqual(run_source(src), [1, 3, 4, 5])

    def test_break_nested_loops(self):
        src = 'let k = 0\nrepeat 2\nk = 0\nwhile true\nk = k + 1\nif k == 3\nbreak\nend\nend\nprint k\nend' + "\n"
        self.assertEqual(run_source(src), [3, 3])

    def test_bengali_break_continue(self):
        src = 'সংখ্যা i = 0\nযতক্ষণ i < 6\ni = i + 1\nযদি i == 2\nচালিয়ে_যাও\nশেষ\nযদি i == 5\nথামো\nশেষ\nদেখাও i\nশেষ' + "\n"
        self.assertEqual(run_source(src), [1, 3, 4])

    def test_break_outside_loop(self):
        with self.assertRaises(SyntaxError):
            run_source("break\n")

    def test_return_inside_loop(self):
        src = 'function find(limit)\nlet i = 0\nrepeat 100\ni = i + 1\nif i == limit\nreturn i\nend\nend\nreturn 0\nend\nprint find(3)\nprint find(200)\n'
        self.assertEqual(run_source(src), [3, 0])

    def test_while_with_if_else(self):
        src = (
            "let i = 0\n"
            "while i < 3\n"
            "if i == 1\n"
            "print 10\n"
            "else\n"
            "print i\n"
            "end\n"
            "i = i + 1\n"
            "end\n"
        )
        self.assertEqual(run_source(src), [0, 10, 2])








if __name__ == "__main__":
    unittest.main(verbosity=2)







