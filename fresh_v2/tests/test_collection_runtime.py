import unittest
from bb import run_source


class CollectionRuntimeTests(unittest.TestCase):

    def test_nested_list_and_dict_read(self):
        source = '''
let data = [{"items": [10, 20]}, {"items": [30, 40]}]
print data[0]["items"][1]
print data[1]["items"][0]
'''
        self.assertEqual(run_source(source), [20, 30])

    def test_nested_collection_assignment(self):
        source = '''
let matrix = [[1, 2], [3, 4]]
matrix[1] = [8, 9]
print matrix[1][0]
print matrix[1][1]
'''
        self.assertEqual(run_source(source), [8, 9])

    def test_dict_new_key_assignment(self):
        source = '''
let d = {"a": 1}
d["b"] = 2
print d["a"]
print d["b"]
'''
        self.assertEqual(run_source(source), [1, 2])

    def test_list_read_out_of_bounds(self):
        with self.assertRaisesRegex(RuntimeError, "ইনডেক্স সীমার বাইরে"):
            run_source('''
let xs = [10, 20]
print xs[2]
''')

    def test_list_assignment_out_of_bounds(self):
        with self.assertRaisesRegex(RuntimeError, "ইনডেক্স সীমার বাইরে"):
            run_source('''
let xs = [10, 20]
xs[2] = 30
''')

    def test_negative_list_read_index(self):
        with self.assertRaisesRegex(RuntimeError, "ইনডেক্স সীমার বাইরে"):
            run_source('''
let xs = [10, 20]
print xs[-1]
''')

    def test_negative_list_assignment_index(self):
        with self.assertRaisesRegex(RuntimeError, "ইনডেক্স সীমার বাইরে"):
            run_source('''
let xs = [10, 20]
xs[-1] = 30
''')

    def test_missing_dict_key(self):
        with self.assertRaisesRegex(RuntimeError, "Dictionary-তে চাবি নেই"):
            run_source('''
let d = {"a": 1}
print d["missing"]
''')

    def test_string_index_out_of_bounds(self):
        with self.assertRaisesRegex(RuntimeError, "ইনডেক্স সীমার বাইরে"):
            run_source('''
let s = "hello"
print s[5]
''')


if __name__ == "__main__":
    unittest.main()
