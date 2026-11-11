import unittest
from bb import run_source


class BuiltinErrorTests(unittest.TestCase):
    def test_length_of_number_is_runtime_error(self):
        src = "সংখ্যা x = 5\nদেখাও দৈর্ঘ্য(x)\n"
        with self.assertRaises(RuntimeError):
            run_source(src)

    def test_keys_of_list_is_runtime_error(self):
        src = "let a = [1, 2]\nprint keys(a)\n"
        with self.assertRaises(RuntimeError):
            run_source(src)

    def test_append_returns_new_list(self):
        src = "let a = [1]\nlet b = append(a, 2)\nprint a\nprint b\n"
        self.assertEqual(run_source(src), [[1], [1, 2]])


if __name__ == "__main__":
    unittest.main()


class CallStatementTests(unittest.TestCase):
    def test_call_statement_discards_result(self):
        src = "ফাংশন f()\nদেখাও 5\nফেরত 1\nশেষ\nf()\nদেখাও 9\n"
        self.assertEqual(run_source(src), [5, 9])


class RepeatCountTests(unittest.TestCase):
    def test_non_finite_repeat_count_is_runtime_error(self):
        from runtime.vm import VirtualMachine

        for bad in (float("inf"), float("nan")):
            prog = {"format": "BB-V2-BC", "functions": {}, "code": [
                {"op": "CONST", "value": bad},
                {"op": "LOOP_BEGIN", "target": 3},
                {"op": "LOOP_NEXT", "target": 2},
            ]}
            with self.assertRaises(RuntimeError):
                VirtualMachine().run(prog)


class SequenceOperatorTests(unittest.TestCase):
    def test_list_concat(self):
        self.assertEqual(run_source("দেখাও [1] + [2]\n"), [[1, 2]])

    def test_string_repeat(self):
        self.assertEqual(run_source('দেখাও "ab" * 3\n'), ["ababab"])

    def test_list_repeat(self):
        self.assertEqual(run_source("দেখাও [0] * 3\n"), [[0, 0, 0]])

    def test_repeat_with_integer_first(self):
        self.assertEqual(run_source('দেখাও 2 * "x"\n'), ["xx"])

    def test_same_result_through_function(self):
        src = "ফাংশন f(a)\nফেরত a * 2\nশেষ\nদেখাও f(\"ab\")\n"
        self.assertEqual(run_source(src), ["abab"])
