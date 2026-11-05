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
    return "unknown"


def length(value):
    if not isinstance(value, str):
        raise TypeError("দৈর্ঘ্য() বর্তমানে শুধু String গ্রহণ করে")
    return len(value)


BUILTINS = {
    "ধরন": (1, type_of),
    "type_of": (1, type_of),
    "দৈর্ঘ্য": (1, length),
    "length": (1, length),
}
