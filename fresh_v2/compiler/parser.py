from . import ast_nodes as A
import ast as py_ast

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.current()
        if token.kind != "EOF":
            self.pos += 1
        return token

    def expect(self, kind):
        token = self.current()
        if token.kind != kind:
            raise SyntaxError(
                f"Line {token.line}: expected {kind}, got {token.value!r}"
            )
        return self.advance()

    def expect_op(self, value):
        token = self.expect("OP")
        if token.value != value:
            raise SyntaxError(
                f"Line {token.line}: expected {value!r}"
            )

    def newlines(self):
        while self.current().kind == "NEWLINE":
            self.advance()

    def line_end(self):
        if self.current().kind not in ("NEWLINE", "EOF"):
            t = self.current()
            raise SyntaxError(f"Line {t.line}: unexpected {t.value!r}")
        self.newlines()

    def block(self, stops):
        statements = []
        self.newlines()

        while self.current().kind not in stops:
            if self.current().kind == "EOF":
                raise SyntaxError("Unexpected EOF: block is not closed")
            statements.append(self.statement())
            self.line_end()

        return statements

    def parse(self):
        statements = self.block({"EOF"})
        return A.Program(statements)

    def statement(self):
        kind = self.current().kind

        if kind == "LET":
            self.advance()
            name = self.expect("IDENT").value
            self.expect_op("=")
            return A.Declare(name, self.expression())

        if kind == "PRINT":
            self.advance()
            return A.Print(self.expression())

        if kind == "BREAK":
            self.advance()
            return A.Break()

        if kind == "CONTINUE":
            self.advance()
            return A.Continue()

        if kind == "GLOBAL":
            self.advance()
            return A.Global(self.expect("IDENT").value)

        if kind == "RETURN":
            self.advance()
            return A.Return(self.expression())

        if kind == "IF":
            self.advance()
            condition = self.expression()
            self.line_end()
            body = self.block({"ELSE", "END"})
            otherwise = []

            if self.current().kind == "ELSE":
                self.advance()
                self.line_end()
                otherwise = self.block({"END"})

            self.expect("END")
            return A.If(condition, body, otherwise)

        if kind == "REPEAT":
            self.advance()
            count = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Repeat(count, body)

        if kind == "WHILE":
            self.advance()
            condition = self.expression()
            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.While(condition, body)

        if kind == "FUNCTION":
            self.advance()
            name = self.expect("IDENT").value
            self.expect_op("(")
            params = []

            if not (self.current().kind == "OP"
                    and self.current().value == ")"):
                params.append(self.expect("IDENT").value)
                while (self.current().kind == "OP"
                       and self.current().value == ","):
                    self.advance()
                    params.append(self.expect("IDENT").value)

            self.expect_op(")")
            if len(params) != len(set(params)):
                raise SyntaxError(f"Duplicate parameter in {name}")

            self.line_end()
            body = self.block({"END"})
            self.expect("END")
            return A.Function(name, params, body)

        if kind == "IDENT":
            name = self.advance().value
            self.expect_op("=")
            return A.Assign(name, self.expression())

        t = self.current()
        raise SyntaxError(
            f"Line {t.line}: unknown statement {t.value!r}"
        )

    def expression(self, minimum=0):
        left = self.prefix()

        precedence = {
            "==": 1, "!=": 1, "<": 1, ">": 1,
            "<=": 1, ">=": 1,
            "+": 2, "-": 2,
            "*": 3, "/": 3, "%": 3,
        }

        while True:
            if (self.current().kind == "OP"
                    and self.current().value == "("):
                if not isinstance(left, A.Variable):
                    break
                self.advance()
                args = []

                if not (self.current().kind == "OP"
                        and self.current().value == ")"):
                    args.append(self.expression())
                    while (self.current().kind == "OP"
                           and self.current().value == ","):
                        self.advance()
                        args.append(self.expression())

                self.expect_op(")")
                left = A.Call(left.name, args)
                continue

            if self.current().kind != "OP":
                break

            op = self.current().value
            level = precedence.get(op, -1)

            if level < minimum:
                break

            self.advance()
            right = self.expression(level + 1)
            left = A.Binary(left, op, right)

        return left

    def prefix(self):
        token = self.advance()

        if token.kind == "NUMBER":
            value = float(token.value) if "." in token.value else int(token.value)
            return A.Number(value)

        if token.kind == "STRING":
            return A.String(py_ast.literal_eval(token.value))

        if token.kind == "TRUE":
            return A.Boolean(True)

        if token.kind == "FALSE":
            return A.Boolean(False)

        if token.kind == "IDENT":
            return A.Variable(token.value)

        if token.kind == "OP" and token.value in ("-", "+"):
            return A.Unary(token.value, self.expression(4))

        if token.kind == "OP" and token.value == "(":
            value = self.expression()
            self.expect_op(")")
            return value

        raise SyntaxError(
            f"Line {token.line}: invalid expression {token.value!r}"
        )

def parse(tokens):
    return Parser(tokens).parse()
