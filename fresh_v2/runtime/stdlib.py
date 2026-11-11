MAX_COLLECTION = 100000


def type_of(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    return "unknown"


def length(value):
    if not isinstance(value, (str, list, dict)):
        raise TypeError("দৈর্ঘ্য() শুধু String, List বা Dictionary গ্রহণ করে")
    return len(value)


def append(items, value):
    if not isinstance(items, list):
        raise TypeError("যোগ_করো() প্রথম মান List হতে হবে")
    if len(items) >= MAX_COLLECTION:
        raise RuntimeError("List অতিরিক্ত বড়")
    return items + [value]


def keys(mapping):
    if not isinstance(mapping, dict):
        raise TypeError("চাবি() শুধু Dictionary গ্রহণ করে")
    return list(mapping.keys())




def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name}() সংখ্যাসূচক মান গ্রহণ করে")
    return value


def absolute(value):
    return abs(_number(value, "abs"))


def rounded(value):
    return round(_number(value, "round"))


def floor_number(value):
    import math
    return math.floor(_number(value, "floor"))


def ceil_number(value):
    import math
    return math.ceil(_number(value, "ceil"))


def square_root(value):
    import math
    value = _number(value, "sqrt")
    if value < 0:
        raise ValueError("sqrt() ঋণাত্মক সংখ্যা গ্রহণ করে না")
    return math.sqrt(value)


def _string(value, name):
    if not isinstance(value, str):
        raise TypeError(f"{name}() String গ্রহণ করে")
    return value


def string_upper(value):
    return _string(value, "upper").upper()


def string_lower(value):
    return _string(value, "lower").lower()


def string_strip(value):
    return _string(value, "strip").strip()


def contains(container, item):
    if not isinstance(container, (str, list, dict)):
        raise TypeError("contains() প্রথম মান String, List বা Dictionary হতে হবে")
    return item in container


def string_replace(value, old, new):
    value = _string(value, "replace")
    old = _string(old, "replace")
    new = _string(new, "replace")
    return value.replace(old, new)



def _list(value, name):
    if not isinstance(value, list):
        raise TypeError(f"{name}() List গ্রহণ করে")
    return value


def reverse_list(items):
    return list(reversed(_list(items, "reverse")))


def sort_list(items):
    items = _list(items, "sort")
    try:
        result = sorted(items)
    except TypeError:
        raise TypeError("sort() List-এর মানগুলো পরস্পর তুলনাযোগ্য হতে হবে") from None
    return result


def remove_item(items, value):
    result = list(_list(items, "remove"))
    try:
        result.remove(value)
    except ValueError:
        raise ValueError("remove() মানটি List-এ পাওয়া যায়নি") from None
    return result


def insert_item(items, index, value):
    items = _list(items, "insert")
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError("insert() Index অবশ্যই Integer হতে হবে")
    if index < 0 or index > len(items):
        raise ValueError("insert() Index সীমার বাইরে")
    if len(items) >= MAX_COLLECTION:
        raise RuntimeError("List অতিরিক্ত বড়")
    result = list(items)
    result.insert(index, value)
    return result


def dict_values(mapping):
    if not isinstance(mapping, dict):
        raise TypeError("values() শুধু Dictionary গ্রহণ করে")
    return list(mapping.values())


def has_key(mapping, key):
    if not isinstance(mapping, dict):
        raise TypeError("has_key() শুধু Dictionary গ্রহণ করে")
    return key in mapping


def get_value(mapping, key):
    if not isinstance(mapping, dict):
        raise TypeError("get() শুধু Dictionary গ্রহণ করে")
    return mapping.get(key)

BUILTINS = {
    "ধরন": (1, type_of),
    "type_of": (1, type_of),
    "দৈর্ঘ্য": (1, length),
    "length": (1, length),
    "যোগ_করো": (2, append),
    "append": (2, append),
    "চাবি": (1, keys),
    "keys": (1, keys),

    "পরম": (1, absolute),
    "abs": (1, absolute),
    "পূর্ণ_রাউন্ড": (1, rounded),
    "round": (1, rounded),
    "নিচের_পূর্ণ": (1, floor_number),
    "floor": (1, floor_number),
    "উপরের_পূর্ণ": (1, ceil_number),
    "ceil": (1, ceil_number),
    "বর্গমূল": (1, square_root),
    "sqrt": (1, square_root),

    "বড়_হাতের": (1, string_upper),
    "upper": (1, string_upper),
    "ছোট_হাতের": (1, string_lower),
    "lower": (1, string_lower),
    "ছাঁটো": (1, string_strip),
    "strip": (1, string_strip),
    "আছে_কি": (2, contains),
    "contains": (2, contains),
    "প্রতিস্থাপন": (3, string_replace),
    "replace": (3, string_replace),
    "উল্টাও": (1, reverse_list),
    "reverse": (1, reverse_list),
    "সাজাও": (1, sort_list),
    "sort": (1, sort_list),
    "বাদ_দাও": (2, remove_item),
    "remove": (2, remove_item),
    "ঢোকাও": (3, insert_item),
    "insert": (3, insert_item),
    "মানসমূহ": (1, dict_values),
    "values": (1, dict_values),
    "চাবি_আছে_কি": (2, has_key),
    "has_key": (2, has_key),
    "নাও_মান": (2, get_value),
    "get": (2, get_value),

}
