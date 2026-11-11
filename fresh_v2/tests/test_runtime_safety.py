import unittest

from runtime.vm import VirtualMachine


class RuntimeSafetyTests(unittest.TestCase):

    def run_code(self, code, functions=None):
        program = {
            "format": "BB-V2-BC",
            "code": code,
            "functions": functions or {},
        }
        return VirtualMachine().run(program)

    def test_execution_step_limit(self):
        with self.assertRaisesRegex(RuntimeError, "Execution step limit"):
            self.run_code([
                {"op": "JUMP", "target": 0},
            ])

    def test_stack_limit(self):
        code = [
            {"op": "CONST", "value": 1}
            for _ in range(10002)
        ]
        with self.assertRaisesRegex(RuntimeError, "Stack limit"):
            self.run_code(code)

    def test_list_build_limit(self):
        with self.assertRaisesRegex(RuntimeError, "List অতিরিক্ত বড়"):
            self.run_code([
                {"op": "BUILD_LIST", "count": 100001},
            ])

    def test_dictionary_build_limit(self):
        with self.assertRaisesRegex(RuntimeError, "Dictionary অতিরিক্ত বড়"):
            self.run_code([
                {"op": "BUILD_DICT", "count": 100001},
            ])

    def test_list_repeat_limit(self):
        with self.assertRaisesRegex(RuntimeError, "List অতিরিক্ত বড়"):
            self.run_code([
                {"op": "CONST", "value": [0]},
                {"op": "CONST", "value": 100001},
                {"op": "BINARY", "operator": "*"},
            ])

    def test_string_repeat_limit(self):
        with self.assertRaisesRegex(RuntimeError, "String অতিরিক্ত বড়"):
            self.run_code([
                {"op": "CONST", "value": "x"},
                {"op": "CONST", "value": 1000001},
                {"op": "BINARY", "operator": "*"},
            ])

    def test_integer_size_limit(self):
        with self.assertRaisesRegex(RuntimeError, "সংখ্যা অতিরিক্ত বড়"):
            self.run_code([
                {"op": "CONST", "value": 1 << 4096},
                {"op": "CONST", "value": 0},
                {"op": "BINARY", "operator": "+"},
            ])

    def test_negative_repeat_count(self):
        with self.assertRaisesRegex(RuntimeError, "REPEAT count"):
            self.run_code([
                {"op": "CONST", "value": -1},
                {"op": "LOOP_BEGIN", "target": 3},
                {"op": "LOOP_NEXT", "target": 2},
            ])

    def test_fractional_repeat_count(self):
        with self.assertRaisesRegex(RuntimeError, "REPEAT count"):
            self.run_code([
                {"op": "CONST", "value": 1.5},
                {"op": "LOOP_BEGIN", "target": 3},
                {"op": "LOOP_NEXT", "target": 2},
            ])

    def test_unknown_function(self):
        with self.assertRaisesRegex(RuntimeError, "Unknown function"):
            self.run_code([
                {"op": "CALL", "name": "missing_function", "argc": 0},
            ])

    def test_function_argument_mismatch(self):
        with self.assertRaisesRegex(RuntimeError, "argument mismatch"):
            self.run_code(
                [{"op": "CALL", "name": "f", "argc": 0}],
                {"f": {"params": ["x"], "target": 0}},
            )


    def test_function_call_depth_limit(self):
        with self.assertRaisesRegex(RuntimeError, "Call depth exceeded"):
            self.run_code(
                [{"op": "CALL", "name": "f", "argc": 0}],
                {"f": {"params": [], "target": 0}},
            )



    def test_unknown_function_preserves_stack(self):
        vm = VirtualMachine()
        program = {
            "format": "BB-V2-BC",
            "code": [
                {"op": "CONST", "value": 77},
                {"op": "CALL", "name": "missing_function", "argc": 1},
            ],
            "functions": {},
        }
        with self.assertRaisesRegex(RuntimeError, "Unknown function"):
            vm.run(program)
        self.assertEqual(vm.stack, [77])

    def test_function_argument_mismatch_preserves_stack(self):
        vm = VirtualMachine()
        program = {
            "format": "BB-V2-BC",
            "code": [
                {"op": "CONST", "value": 77},
                {"op": "CALL", "name": "f", "argc": 1},
            ],
            "functions": {
                "f": {"params": [], "target": 0},
            },
        }
        with self.assertRaisesRegex(RuntimeError, "argument mismatch"):
            vm.run(program)
        self.assertEqual(vm.stack, [77])

    def test_input_callback_failure_preserves_stack(self):
        def failing_input(prompt):
            raise ValueError("input failed")

        vm = VirtualMachine(input_fn=failing_input)
        program = {
            "format": "BB-V2-BC",
            "code": [
                {"op": "CONST", "value": "prompt"},
                {"op": "CALL", "name": "input", "argc": 1},
            ],
            "functions": {},
        }
        with self.assertRaises(ValueError):
            vm.run(program)
        self.assertEqual(vm.stack, ["prompt"])

if __name__ == "__main__":
    unittest.main()
