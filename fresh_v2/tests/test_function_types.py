import unittest
from bb import compile_source, run_source


class FunctionTypeTests(unittest.TestCase):

    def test_integer_return(self):
        source = """function add(x)
return x + 1
end
print add(5)
"""
        compile_source(source)

    def test_string_return(self):
        source = '''function greet(x)
return x + "!"
end
print greet("Hi")
'''
        compile_source(source)

    def test_reject_wrong_argument_type(self):
        source = '''function add(x)
return x + 1
end
print add("hello")
'''
        with self.assertRaises(TypeError):
            compile_source(source)

    def test_mixed_return_types_allowed(self):
        source = '''function choose(x)
if x > 0
return 1
else
return "bad"
end
end
print choose(1)
'''
        compile_source(source)

    def test_numeric_return_types_allowed(self):
        source = '''function choose(x)
if x > 0
return 1
else
return 2.5
end
end
print choose(1)
'''
        compile_source(source)

    def test_mixed_return_runtime(self):
        source = '''function choose(x)
if x > 0
return 1
else
return "bad"
end
end
print choose(1)
print choose(-1)
'''
        self.assertEqual(run_source(source), [1, "bad"])


if __name__ == "__main__":
    unittest.main()
