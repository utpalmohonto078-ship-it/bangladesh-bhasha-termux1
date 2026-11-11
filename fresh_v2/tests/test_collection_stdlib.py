import pytest
from bb import run_source


@pytest.mark.parametrize("name", ["reverse", "উল্টাও"])
def test_reverse(name):
    assert run_source(f"দেখাও {name}([1, 2, 3])") == [[3, 2, 1]]


@pytest.mark.parametrize("name", ["sort", "সাজাও"])
def test_sort(name):
    assert run_source(f"দেখাও {name}([3, 1, 2])") == [[1, 2, 3]]


@pytest.mark.parametrize("name", ["remove", "বাদ_দাও"])
def test_remove(name):
    src = f'''
let a = [1, 2, 2, 3]
দেখাও {name}(a, 2)
দেখাও a
'''
    assert run_source(src) == [[1, 2, 3], [1, 2, 2, 3]]


@pytest.mark.parametrize("name", ["insert", "ঢোকাও"])
def test_insert(name):
    src = f'''
let a = [1, 3]
দেখাও {name}(a, 1, 2)
দেখাও a
'''
    assert run_source(src) == [[1, 2, 3], [1, 3]]


@pytest.mark.parametrize("name", ["values", "মানসমূহ"])
def test_values(name):
    assert run_source(
        f'দেখাও {name}({{"a": 10, "b": 20}})'
    ) == [[10, 20]]


@pytest.mark.parametrize("name", ["has_key", "চাবি_আছে_কি"])
def test_has_key(name):
    src = f'''
let d = {{"a": 10}}
দেখাও {name}(d, "a")
দেখাও {name}(d, "missing")
'''
    assert run_source(src) == [True, False]


@pytest.mark.parametrize("name", ["get", "নাও_মান"])
def test_get(name):
    src = f'''
let d = {{"a": 10}}
দেখাও {name}(d, "a")
দেখাও {name}(d, "missing")
'''
    assert run_source(src) == [10, None]


def test_sort_rejects_incomparable_values():
    with pytest.raises(RuntimeError):
        run_source('দেখাও sort([1, "a"])')


def test_remove_rejects_missing_value():
    with pytest.raises(RuntimeError):
        run_source('দেখাও remove([1, 2], 9)')


def test_insert_rejects_bad_index():
    with pytest.raises(RuntimeError):
        run_source('দেখাও insert([1, 2], -1, 9)')


def test_insert_rejects_non_integer_index():
    with pytest.raises(RuntimeError):
        run_source('দেখাও insert([1, 2], "1", 9)')


@pytest.mark.parametrize("source", [
    'দেখাও reverse("abc")',
    'দেখাও sort("abc")',
    'দেখাও remove("abc", "a")',
    'দেখাও insert("abc", 0, "x")',
    'দেখাও values([1, 2])',
    'দেখাও has_key([1], 1)',
    'দেখাও get([1], 0)',
])
def test_collection_builtins_reject_wrong_container(source):
    with pytest.raises(RuntimeError):
        run_source(source)
