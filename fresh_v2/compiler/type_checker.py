from . import ast_nodes as A

NUMERIC = {"integer", "float"}
UNKNOWN = "unknown"


def compatible(expected, actual):
    if expected == UNKNOWN or actual == UNKNOWN:
        return True
    if expected == actual:
        return True
    return expected == "float" and actual == "integer"


def check_types(program):
    globals_types = {}
    functions = {
        stmt.name: stmt
        for stmt in program.statements
        if isinstance(stmt, A.Function)
    }

    def infer(node, scope):
        if isinstance(node, A.Number):
            return "float" if isinstance(node.value, float) else "integer"

        if isinstance(node, A.String):
            return "string"

        if isinstance(node, A.Boolean):
            return "boolean"

        if isinstance(node, A.Variable):
            if node.name in scope:
                return scope[node.name]
            if node.name in globals_types:
                return globals_types[node.name]
            return UNKNOWN

        if isinstance(node, A.Call):
            for arg in node.args:
                infer(arg, scope)

            if node.name in functions:
                return check_function(node.name, [infer(a, scope) for a in node.args])
            if node.name in ("ধরন", "type_of"):
                return "string"
            if node.name in ("দৈর্ঘ্য", "length"):
                return "integer"
            return UNKNOWN

        if isinstance(node, A.Unary):
            value_type = infer(node.operand, scope)
            if value_type != UNKNOWN and value_type not in NUMERIC:
                raise TypeError(
                    f"Unary {node.operator}: numeric value required, got {value_type}"
                )
            return value_type

        if isinstance(node, A.Binary):
            left = infer(node.left, scope)
            right = infer(node.right, scope)
            op = node.operator

            if op in ("+", "-", "*", "/", "%"):
                if op == "+" and left == right == "string":
                    return "string"

                if op == "+" and "string" in (left, right) and UNKNOWN in (left, right):
                    return UNKNOWN
                if left != UNKNOWN and left not in NUMERIC:
                    raise TypeError(
                        f"Operator {op}: numeric value required, got {left}"
                    )
                if right != UNKNOWN and right not in NUMERIC:
                    raise TypeError(
                        f"Operator {op}: numeric value required, got {right}"
                    )

                if left == UNKNOWN or right == UNKNOWN:
                    return UNKNOWN
                if op == "/":
                    return "float"
                return "float" if "float" in (left, right) else "integer"

            if op in ("==", "!=", "<", ">", "<=", ">="):
                if left != UNKNOWN and right != UNKNOWN:
                    same_numeric = left in NUMERIC and right in NUMERIC
                    if left != right and not same_numeric:
                        raise TypeError(
                            f"Incompatible comparison: {left} and {right}"
                        )
                    if op not in ("==", "!=") and not (
                        same_numeric or left == right == "string"
                    ):
                        raise TypeError(
                            f"Operator {op}: values are not order-comparable"
                        )
                return "boolean"

        raise TypeError(
            f"Static type checker: unsupported expression {type(node).__name__}"
        )

    return_stack = []
    fn_cache = {}
    fn_active = set()

    def function_globals(function):
        found = set()
        def walk(body):
            for item in body:
                if isinstance(item, A.Global):
                    found.add(item.name)
                elif isinstance(item, A.If):
                    walk(item.body)
                    walk(item.otherwise)
                elif isinstance(item, (A.Repeat, A.While)):
                    walk(item.body)
        walk(function.body)
        return found

    def merge_returns(types):
        if not types or UNKNOWN in types:
            return UNKNOWN
        unique = set(types)
        if len(unique) == 1:
            return unique.pop()
        if unique <= NUMERIC:
            return "float"
        return UNKNOWN

    def check_function(name, arg_types):
        function = functions[name]
        if len(arg_types) != len(function.params):
            return UNKNOWN
        key = (name, tuple(arg_types))
        if key in fn_cache:
            return fn_cache[key]
        if key in fn_active:
            return UNKNOWN
        fn_active.add(key)
        return_stack.append([])
        try:
            scope = dict(zip(function.params, arg_types))
            check_body(function.body, scope, function_globals(function))
            result = merge_returns(return_stack[-1])
        except TypeError as error:
            raise TypeError(f"{name}({', '.join(arg_types)}): {error}") from None
        finally:
            return_stack.pop()
            fn_active.discard(key)
        fn_cache[key] = result
        return result


    def check_body(body, scope, declared_globals):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                if stmt.name in declared_globals:
                    raise TypeError(
                        f"{stmt.name}: cannot declare a GLOBAL variable locally"
                    )
                value_type = infer(stmt.value, scope)
                scope[stmt.name] = value_type

            elif isinstance(stmt, A.Assign):
                value_type = infer(stmt.value, scope)

                if stmt.name in declared_globals:
                    expected = globals_types.get(stmt.name, UNKNOWN)
                    if not compatible(expected, value_type):
                        raise TypeError(
                            f"{stmt.name}: cannot assign {value_type} "
                            f"to {expected}"
                        )
                elif stmt.name in scope:
                    expected = scope[stmt.name]
                    if not compatible(expected, value_type):
                        raise TypeError(
                            f"{stmt.name}: cannot assign {value_type} "
                            f"to {expected}"
                        )
                elif stmt.name in globals_types:
                    expected = globals_types[stmt.name]
                    if not compatible(expected, value_type):
                        raise TypeError(
                            f"{stmt.name}: cannot assign {value_type} "
                            f"to {expected}"
                        )

            elif isinstance(stmt, A.Print):
                infer(stmt.value, scope)

            elif isinstance(stmt, A.If):
                condition_type = infer(stmt.condition, scope)
                if condition_type not in ("boolean", UNKNOWN):
                    raise TypeError(
                        f"IF condition must be Boolean, got {condition_type}"
                    )
                check_body(stmt.body, scope, declared_globals)
                check_body(stmt.otherwise, scope, declared_globals)

            elif isinstance(stmt, A.While):
                condition_type = infer(stmt.condition, scope)
                if condition_type not in ("boolean", UNKNOWN):
                    raise TypeError(
                        f"WHILE condition must be Boolean, got {condition_type}"
                    )
                check_body(stmt.body, scope, declared_globals)

            elif isinstance(stmt, A.Repeat):
                count_type = infer(stmt.count, scope)
                if count_type not in NUMERIC and count_type != UNKNOWN:
                    raise TypeError(
                        f"REPEAT count must be numeric, got {count_type}"
                    )
                check_body(stmt.body, scope, declared_globals)

            elif isinstance(stmt, A.Return):
                ret_type = infer(stmt.value, scope)
                if return_stack:
                    return_stack[-1].append(ret_type)

            elif isinstance(stmt, A.Global):
                pass

    # Infer global types in declaration order.
    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            globals_types[stmt.name] = infer(stmt.value, globals_types)

    # Check functions. Unknown parameter types preserve compatibility.
    for function in functions.values():
        scope = {name: UNKNOWN for name in function.params}
        declared_globals = set()

        def collect_globals(body):
            for item in body:
                if isinstance(item, A.Global):
                    declared_globals.add(item.name)
                elif isinstance(item, A.If):
                    collect_globals(item.body)
                    collect_globals(item.otherwise)
                elif isinstance(item, (A.Repeat, A.While)):
                    collect_globals(item.body)

        collect_globals(function.body)
        check_body(function.body, scope, declared_globals)

    # Check top-level executable statements.
    scope = dict(globals_types)
    for stmt in program.statements:
        if not isinstance(stmt, (A.Declare, A.Function)):
            check_body([stmt], scope, set())

    return True
