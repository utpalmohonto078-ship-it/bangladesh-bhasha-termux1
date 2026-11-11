import unittest
from bb import run_source, compile_source


class CollectionTests(unittest.TestCase):

    def test_list_index_read_and_assignment(self):
        source = """
let xs = [10, 20]
xs[1] = 30
print xs[1]
"""
        self.assertEqual(run_source(source), [30])

    def test_dict_index_read_and_assignment(self):
        source = '''
let d = {"a": 1}
d["a"] = 2
print d["a"]
'''
        self.assertEqual(run_source(source), [2])

    def test_reject_boolean_dict_read_key(self):
        source = '''
let d = {"a": 1}
print d[সত্য]
'''
        with self.assertRaises(TypeError):
            compile_source(source)

    def test_reject_boolean_dict_assignment_key(self):
        source = '''
let d = {"a": 1}
d[সত্য] = 2
'''
        with self.assertRaises(TypeError):
            compile_source(source)

    def test_reject_string_list_assignment_index(self):
        source = '''
let xs = [10, 20]
xs["bad"] = 30
'''
        with self.assertRaises(TypeError):
            compile_source(source)


if __name__ == "__main__":
    unittest.main()
