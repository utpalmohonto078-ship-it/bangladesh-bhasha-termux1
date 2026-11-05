import unittest
from bb import compile_source, run_source


class StaticTypeTests(unittest.TestCase):

    def test_integer_float_compatible(self):
        self.assertEqual(run_source(
            "সংখ্যা x = 5\nদেখাও x + 2.5\n"
        ), [7.5])

    def test_string_concatenation(self):
        self.assertEqual(run_source(
            'দেখাও "Bangla" + "desh"\n'
        ), ["Bangladesh"])

    def test_reject_string_subtraction(self):
        with self.assertRaises(TypeError):
            compile_source('দেখাও "hello" - 2\n')

    def test_reject_boolean_arithmetic(self):
        with self.assertRaises(TypeError):
            compile_source("দেখাও সত্য + 2\n")

    def test_reject_wrong_assignment(self):
        with self.assertRaises(TypeError):
            compile_source(
                'সংখ্যা x = 10\nx = "wrong"\n'
            )

    def test_reject_non_boolean_condition(self):
        with self.assertRaises(TypeError):
            compile_source(
                'যদি "hello"\nদেখাও 1\nশেষ\n'
            )

    def test_reject_string_repeat_count(self):
        with self.assertRaises(TypeError):
            compile_source(
                'পুনরাবৃত্তি "three"\nদেখাও 1\nশেষ\n'
            )

    def test_builtin_types(self):
        self.assertEqual(run_source(
            "দেখাও ধরন(10)\nদেখাও দৈর্ঘ্য(\"বাংলা\")\n"
        ), ["integer", 5])


if __name__ == "__main__":
    unittest.main()
