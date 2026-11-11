import pytest
from bb import run_source


@pytest.mark.parametrize("name", ["abs", "পরম"])
def test_absolute(name):
    assert run_source(f"দেখাও {name}(-8)\n") == [8]


@pytest.mark.parametrize("name", ["round", "পূর্ণ_রাউন্ড"])
def test_round(name):
    assert run_source(f"দেখাও {name}(4.6)\n") == [5]


@pytest.mark.parametrize("name", ["floor", "নিচের_পূর্ণ"])
def test_floor(name):
    assert run_source(f"দেখাও {name}(4.8)\n") == [4]


@pytest.mark.parametrize("name", ["ceil", "উপরের_পূর্ণ"])
def test_ceil(name):
    assert run_source(f"দেখাও {name}(4.2)\n") == [5]


@pytest.mark.parametrize("name", ["sqrt", "বর্গমূল"])
def test_sqrt(name):
    assert run_source(f"দেখাও {name}(25)\n") == [5.0]


@pytest.mark.parametrize("name", ["upper", "বড়_হাতের"])
def test_upper(name):
    assert run_source(f'দেখাও {name}("hello")\n') == ["HELLO"]


@pytest.mark.parametrize("name", ["lower", "ছোট_হাতের"])
def test_lower(name):
    assert run_source(f'দেখাও {name}("HELLO")\n') == ["hello"]


@pytest.mark.parametrize("name", ["strip", "ছাঁটো"])
def test_strip(name):
    assert run_source(f'দেখাও {name}("  hello  ")\n') == ["hello"]


@pytest.mark.parametrize("name", ["contains", "আছে_কি"])
def test_contains(name):
    assert run_source(f'দেখাও {name}("bangladesh", "desh")\n') == [True]


@pytest.mark.parametrize("name", ["replace", "প্রতিস্থাপন"])
def test_replace(name):
    assert run_source(f'দেখাও {name}("hello world", "world", "BB")\n') == ["hello BB"]


def test_sqrt_negative_rejected():
    with pytest.raises(RuntimeError):
        run_source("দেখাও sqrt(-1)\n")


def test_math_rejects_string():
    with pytest.raises(RuntimeError):
        run_source('দেখাও abs("5")\n')


def test_replace_rejects_non_string():
    with pytest.raises(RuntimeError):
        run_source('দেখাও replace("hello", 5, "x")\n')
