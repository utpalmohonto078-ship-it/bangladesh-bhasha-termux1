import unittest
from bb import compile_source, run_source


class InputBuiltinTests(unittest.TestCase):
    def test_bengali_input_without_prompt(self):
        self.assertEqual(
            run_source("দেখাও নাও()\n", input_fn=lambda prompt: "বাংলা"),
            ["বাংলা"],
        )

    def test_bengali_input_with_prompt(self):
        prompts = []
        def fake_input(prompt):
            prompts.append(prompt)
            return "উৎপল"

        result = run_source(
            'দেখাও নাও("নাম লিখুন: ")\n',
            input_fn=fake_input,
        )
        self.assertEqual(result, ["উৎপল"])
        self.assertEqual(prompts, ["নাম লিখুন: "])

    def test_english_input_alias(self):
        self.assertEqual(
            run_source(
                'print input("Name: ")\n',
                input_fn=lambda prompt: "Utpal",
            ),
            ["Utpal"],
        )

    def test_input_returns_string(self):
        self.assertEqual(
            run_source(
                'দেখাও নাও() + "!"\n',
                input_fn=lambda prompt: "হ্যালো",
            ),
            ["হ্যালো!"],
        )

    def test_too_many_arguments_rejected(self):
        with self.assertRaises(TypeError):
            compile_source('দেখাও নাও("a", "b")\n')


if __name__ == "__main__":
    unittest.main()
