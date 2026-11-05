from . import ast_nodes as A

def analyze(program):
    top_globals = set()
    functions = {}

    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            if stmt.name in top_globals:
                raise NameError(f"Duplicate variable: {stmt.name}")
            top_globals.add(stmt.name)

        elif isinstance(stmt, A.Function):
            if stmt.name in functions:
                raise NameError(f"Duplicate function: {stmt.name}")
            functions[stmt.name] = stmt

    def collect_globals(body, result):
        for stmt in body:
            if isinstance(stmt, A.Global):
                result.add(stmt.name)
            elif isinstance(stmt, A.If):
                collect_globals(stmt.body, result)
                collect_globals(stmt.otherwise, result)
            elif isinstance(stmt, A.Repeat):
                collect_globals(stmt.body, result)
            elif isinstance(stmt, A.While):
                collect_globals(stmt.body, result)

    def collect_locals(body, result):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                result.add(stmt.name)
            elif isinstance(stmt, A.If):
                collect_locals(stmt.body, result)
                collect_locals(stmt.otherwise, result)
            elif isinstance(stmt, A.Repeat):
                collect_locals(stmt.body, result)
            elif isinstance(stmt, A.While):
                collect_locals(stmt.body, result)

    def expression(node, scope, in_function):
        if isinstance(node, A.Variable):
            if node.name not in scope and node.name not in top_globals:
                raise NameError(f"Undefined variable: {node.name}")

        elif isinstance(node, A.Call):
            if node.name not in functions:
                raise NameError(f"Unknown function: {node.name}")
            expected = len(functions[node.name].params)
            if len(node.args) != expected:
                raise TypeError(
                    f"{node.name}: expected {expected} arguments, "
                    f"got {len(node.args)}"
                )
            for arg in node.args:
                expression(arg, scope, in_function)

        elif isinstance(node, A.Binary):
            expression(node.left, scope, in_function)
            expression(node.right, scope, in_function)

        elif isinstance(node, A.Unary):
            expression(node.operand, scope, in_function)

        elif not isinstance(node, (A.Number, A.String, A.Boolean)):
            raise TypeError(f"Unsupported expression: {type(node).__name__}")

    def statements(body, scope, in_function, declared_globals):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                if stmt.name in scope:
                    raise NameError(f"Duplicate local variable: {stmt.name}")
                if stmt.name in declared_globals:
                    raise NameError(f"{stmt.name} is declared GLOBAL")
                expression(stmt.value, scope, in_function)
                scope.add(stmt.name)

            elif isinstance(stmt, A.Assign):
                if (stmt.name not in scope and stmt.name not in declared_globals
                    and (in_function or stmt.name not in top_globals)):
                    raise NameError(f"Assignment to undeclared variable: {stmt.name}")
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.Print):
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.If):
                expression(stmt.condition, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)
                statements(stmt.otherwise, scope, in_function, declared_globals)

            elif isinstance(stmt, A.Repeat):
                expression(stmt.count, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)

            elif isinstance(stmt, A.While):
                expression(stmt.condition, scope, in_function)
                statements(stmt.body, scope, in_function, declared_globals)

            elif isinstance(stmt, A.Return):
                if not in_function:
                    raise SyntaxError("RETURN outside function")
                expression(stmt.value, scope, in_function)

            elif isinstance(stmt, A.Global):
                if not in_function:
                    raise SyntaxError("GLOBAL outside function")
                if stmt.name not in top_globals:
                    raise NameError(f"Unknown global variable: {stmt.name}")

    for stmt in program.statements:
        if isinstance(stmt, A.Function):
            globals_set = set()
            collect_globals(stmt.body, globals_set)

            if globals_set.intersection(stmt.params):
                raise SyntaxError("GLOBAL cannot conflict with a parameter")

            locals_set = set(stmt.params)
            collect_locals(stmt.body, locals_set)

            if globals_set.intersection(locals_set):
                raise SyntaxError("GLOBAL cannot conflict with a local variable")

            scope = set(stmt.params)
            statements(stmt.body, scope, True, globals_set)

        elif not isinstance(stmt, A.Declare):
            statements([stmt], set(), False, set())

    # Validate initializers after collecting all top-level declarations.
    scope = set()
    for stmt in program.statements:
        if isinstance(stmt, A.Declare):
            expression(stmt.value, scope, False)
            scope.add(stmt.name)

    return True
