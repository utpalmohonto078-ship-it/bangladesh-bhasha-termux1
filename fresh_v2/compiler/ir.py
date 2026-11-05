from . import ast_nodes as A

def generate(program):
    code = []
    functions = {}
    loops = []

    def expr(node):
        if isinstance(node, A.Number):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.String):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Boolean):
            code.append({"op": "CONST", "value": node.value})
        elif isinstance(node, A.Variable):
            code.append({"op": "LOAD", "name": node.name})
        elif isinstance(node, A.Unary):
            expr(node.operand)
            code.append({"op": "UNARY", "operator": node.operator})
        elif isinstance(node, A.Binary):
            expr(node.left)
            expr(node.right)
            code.append({"op": "BINARY", "operator": node.operator})
        elif isinstance(node, A.Call):
            for arg in node.args:
                expr(arg)
            code.append({
                "op": "CALL", "name": node.name, "argc": len(node.args)
            })

    def globals_in(body):
        found = set()
        for stmt in body:
            if isinstance(stmt, A.Global):
                found.add(stmt.name)
            elif isinstance(stmt, A.If):
                found |= globals_in(stmt.body)
                found |= globals_in(stmt.otherwise)
            elif isinstance(stmt, A.Repeat):
                found |= globals_in(stmt.body)
            elif isinstance(stmt, A.While):
                found |= globals_in(stmt.body)
        return found

    def block(body):
        for stmt in body:
            if isinstance(stmt, A.Declare):
                expr(stmt.value)
                code.append({"op": "STORE", "name": stmt.name})

            elif isinstance(stmt, A.Assign):
                expr(stmt.value)
                code.append({"op": "STORE", "name": stmt.name})

            elif isinstance(stmt, A.Print):
                expr(stmt.value)
                code.append({"op": "PRINT"})

            elif isinstance(stmt, A.Return):
                expr(stmt.value)
                code.append({"op": "RETURN"})

            elif isinstance(stmt, A.Global):
                pass

            elif isinstance(stmt, A.If):
                expr(stmt.condition)
                jf = len(code)
                code.append({"op": "JUMP_IF_FALSE", "target": -1})
                block(stmt.body)

                if stmt.otherwise:
                    jmp = len(code)
                    code.append({"op": "JUMP", "target": -1})
                    code[jf]["target"] = len(code)
                    block(stmt.otherwise)
                    code[jmp]["target"] = len(code)
                else:
                    code[jf]["target"] = len(code)

            elif isinstance(stmt, A.Break):
                loop = loops[-1]
                loop["breaks"].append(len(code))
                op = "LOOP_BREAK" if loop["kind"] == "repeat" else "JUMP"
                code.append({"op": op, "target": -1})

            elif isinstance(stmt, A.Continue):
                loop = loops[-1]
                loop["continues"].append(len(code))
                code.append({"op": "JUMP", "target": -1})

            elif isinstance(stmt, A.Repeat):
                expr(stmt.count)
                begin = len(code)
                code.append({"op": "LOOP_BEGIN", "target": -1})
                loops.append({"kind": "repeat", "breaks": [], "continues": []})
                block(stmt.body)
                next_index = len(code)
                code.append({"op": "LOOP_NEXT", "target": begin + 1})
                end = len(code)
                code[begin]["target"] = end
                loop = loops.pop()
                for i in loop["breaks"]:
                    code[i]["target"] = end
                for i in loop["continues"]:
                    code[i]["target"] = next_index

            elif isinstance(stmt, A.While):
                begin = len(code)
                expr(stmt.condition)
                exit_jump = len(code)
                code.append({"op": "JUMP_IF_FALSE", "target": -1})
                loops.append({"kind": "while", "breaks": [], "continues": []})
                block(stmt.body)
                code.append({"op": "JUMP", "target": begin})
                end = len(code)
                code[exit_jump]["target"] = end
                loop = loops.pop()
                for i in loop["breaks"]:
                    code[i]["target"] = end
                for i in loop["continues"]:
                    code[i]["target"] = begin

    # Functions are placed before the main program.
    # A jump prevents normal execution from entering function bodies.
    jump_main = len(code)
    code.append({"op": "JUMP", "target": -1})

    for stmt in program.statements:
        if isinstance(stmt, A.Function):
            functions[stmt.name] = {
                "params": stmt.params,
                "globals": sorted(globals_in(stmt.body)),
                "target": len(code),
            }
            block(stmt.body)
            code.append({"op": "CONST", "value": None})
            code.append({"op": "RETURN"})

    code[jump_main]["target"] = len(code)

    main = [s for s in program.statements if not isinstance(s, A.Function)]
    block(main)

    return {
        "format": "BB-V2-IR",
        "instructions": code,
        "functions": functions,
    }
