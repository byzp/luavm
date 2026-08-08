from __future__ import annotations

from typing import Optional

from .lexer import CompileError, Lexer, Token


class Parser:
    BINARY_PRECEDENCE = {
        "or": (1, False),
        "and": (2, False),
        "<": (3, False),
        ">": (3, False),
        "<=": (3, False),
        ">=": (3, False),
        "==": (3, False),
        "~=": (3, False),
        "..": (4, True),
        "+": (5, False),
        "-": (5, False),
        "*": (6, False),
        "/": (6, False),
        "%": (6, False),
        "^": (8, True),
    }

    def __init__(self, tokens: list[Token], filename: str = "<source>") -> None:
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 0) -> Token:
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def error(self, message: str, token: Optional[Token] = None) -> CompileError:
        token = token or self.current
        return CompileError(f"{self.filename}:{token.line}:{token.column}: {message}")

    def advance(self) -> Token:
        token = self.current
        self.pos += 1
        return token

    def match(self, value: str) -> Optional[Token]:
        if self.current.value == value:
            return self.advance()
        return None

    def expect(self, value: str) -> Token:
        if self.current.value != value:
            raise self.error(f"expected {value!r}, got {self.current.value!r}")
        return self.advance()

    def expect_kind(self, kind: str) -> Token:
        if self.current.kind != kind:
            raise self.error(f"expected {kind}, got {self.current.value!r}")
        return self.advance()

    def parse(self) -> list[tuple]:
        body = self.parse_block({"<eof>"})
        if self.current.kind != "eof":
            raise self.error("unexpected tokens after chunk")
        return body

    def parse_block(self, stops: set[str]) -> list[tuple]:
        statements: list[tuple] = []
        while self.current.kind != "eof" and self.current.value not in stops:
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> tuple:
        token = self.current
        value = token.value
        if self.match(";"):
            return ("nop", token.line)
        if value == "local":
            return self.parse_local()
        if value == "function":
            return self.parse_function_statement()
        if value == "return":
            return self.parse_return()
        if value == "if":
            return self.parse_if()
        if value == "while":
            return self.parse_while()
        if value == "repeat":
            return self.parse_repeat()
        if value == "for":
            return self.parse_for()
        if value == "do":
            self.advance()
            body = self.parse_block({"end"})
            self.expect("end")
            return ("do", token.line, body)
        if value == "break":
            self.advance()
            return ("break", token.line)
        if value in {"end", "else", "elseif", "until"}:
            raise self.error(f"unexpected {value!r}")

        first = self.parse_suffixed_expr()
        if self.current.value in {"=", ","}:
            targets = [first]
            while self.match(","):
                targets.append(self.parse_suffixed_expr())
            self.expect("=")
            values = self.parse_expr_list()
            return ("assign", token.line, targets, values)
        if first[0] not in {"call", "methodcall"}:
            raise self.error("statement must be an assignment or function call", token)
        return ("callstmt", token.line, first)

    def parse_local(self) -> tuple:
        token = self.expect("local")
        if self.match("function"):
            name = self.expect_kind("name")
            params, vararg, body = self.parse_function_body()
            return ("local_function", token.line, name.value, params, vararg, body)
        names = [self.expect_kind("name").value]
        while self.match(","):
            names.append(self.expect_kind("name").value)
        values = self.parse_expr_list() if self.match("=") else []
        return ("local", token.line, names, values)

    def parse_function_statement(self) -> tuple:
        token = self.expect("function")
        name = self.expect_kind("name")
        target: tuple = ("name", name.line, name.value)
        while self.match("."):
            part = self.expect_kind("name")
            target = ("index", part.line, target, ("literal", part.line, part.value))
        method = False
        if self.match(":"):
            part = self.expect_kind("name")
            target = ("index", part.line, target, ("literal", part.line, part.value))
            method = True
        params, vararg, body = self.parse_function_body()
        if method:
            params = ["self", *params]
        return ("function", token.line, target, params, vararg, body)

    def parse_function_body(self) -> tuple[list[str], bool, list[tuple]]:
        self.expect("(")
        params: list[str] = []
        vararg = False
        if not self.match(")"):
            if self.match("..."):
                vararg = True
                self.expect(")")
            else:
                params.append(self.expect_kind("name").value)
                while self.match(","):
                    if self.match("..."):
                        vararg = True
                        break
                    params.append(self.expect_kind("name").value)
                self.expect(")")
        body = self.parse_block({"end"})
        self.expect("end")
        return params, vararg, body

    def parse_return(self) -> tuple:
        token = self.expect("return")
        if (
            self.current.value in {"end", "else", "elseif", "until", ";"}
            or self.current.kind == "eof"
        ):
            self.match(";")
            return ("return", token.line, [])
        values = self.parse_expr_list()
        self.match(";")
        return ("return", token.line, values)

    def parse_if(self) -> tuple:
        token = self.expect("if")
        branches = []
        condition = self.parse_expr()
        self.expect("then")
        branches.append((condition, self.parse_block({"elseif", "else", "end"})))
        while self.match("elseif"):
            condition = self.parse_expr()
            self.expect("then")
            branches.append((condition, self.parse_block({"elseif", "else", "end"})))
        else_body = []
        if self.match("else"):
            else_body = self.parse_block({"end"})
        self.expect("end")
        return ("if", token.line, branches, else_body)

    def parse_while(self) -> tuple:
        token = self.expect("while")
        condition = self.parse_expr()
        self.expect("do")
        body = self.parse_block({"end"})
        self.expect("end")
        return ("while", token.line, condition, body)

    def parse_repeat(self) -> tuple:
        token = self.expect("repeat")
        body = self.parse_block({"until"})
        self.expect("until")
        condition = self.parse_expr()
        return ("repeat", token.line, body, condition)

    def parse_for(self) -> tuple:
        token = self.expect("for")
        name = self.expect_kind("name").value
        if self.match("="):
            start = self.parse_expr()
            self.expect(",")
            limit = self.parse_expr()
            step = self.parse_expr() if self.match(",") else ("literal", token.line, 1)
            self.expect("do")
            body = self.parse_block({"end"})
            self.expect("end")
            return ("for_num", token.line, name, start, limit, step, body)
        names = [name]
        while self.match(","):
            names.append(self.expect_kind("name").value)
        self.expect("in")
        expressions = self.parse_expr_list()
        self.expect("do")
        body = self.parse_block({"end"})
        self.expect("end")
        return ("for_in", token.line, names, expressions, body)

    def parse_expr_list(self) -> list[tuple]:
        values = [self.parse_expr()]
        while self.match(","):
            values.append(self.parse_expr())
        return values

    def parse_expr(self, min_precedence: int = 0) -> tuple:
        left = self.parse_unary_or_primary()
        while True:
            op = self.current.value
            info = self.BINARY_PRECEDENCE.get(op)
            if info is None or info[0] < min_precedence:
                break
            self.advance()
            precedence, right_assoc = info
            right = self.parse_expr(precedence if right_assoc else precedence + 1)
            left = ("binop", left[1], op, left, right)
        return left

    def parse_unary_or_primary(self) -> tuple:
        token = self.current
        if token.kind in {"symbol", "keyword"} and token.value in {"-", "not", "#"}:
            self.advance()
            return ("unop", token.line, token.value, self.parse_expr(7))
        return self.parse_suffixed_expr()

    def parse_suffixed_expr(self) -> tuple:
        expr = self.parse_primary()
        while True:
            if self.match("["):
                key = self.parse_expr()
                self.expect("]")
                expr = ("index", expr[1], expr, key)
            elif self.match("."):
                name = self.expect_kind("name")
                expr = ("index", name.line, expr, ("literal", name.line, name.value))
            elif self.match(":"):
                name = self.expect_kind("name")
                args = self.parse_call_args()
                expr = ("methodcall", name.line, expr, name.value, args)
            elif (
                self.current.value == "("
                or self.current.kind == "string"
                or self.current.value == "{"
            ):
                args = self.parse_call_args()
                expr = ("call", expr[1], expr, args)
            else:
                break
        return expr

    def parse_primary(self) -> tuple:
        token = self.current
        if token.kind == "number" or token.kind == "string":
            self.advance()
            return ("literal", token.line, token.value)
        if token.kind == "name":
            self.advance()
            return ("name", token.line, token.value)
        if token.value in {"nil", "true", "false"}:
            self.advance()
            value = {"nil": None, "true": True, "false": False}[token.value]
            return ("literal", token.line, value)
        if token.value == "...":
            self.advance()
            return ("vararg", token.line)
        if token.value == "function":
            self.advance()
            params, vararg, body = self.parse_function_body()
            return ("function_expr", token.line, params, vararg, body)
        if token.value == "{":
            return self.parse_table()
        if self.match("("):
            expr = self.parse_expr()
            self.expect(")")
            return ("paren", token.line, expr)
        raise self.error(f"expected expression, got {token.value!r}")

    def parse_call_args(self) -> list[tuple]:
        if self.match("("):
            if self.match(")"):
                return []
            args = self.parse_expr_list()
            self.expect(")")
            return args
        if self.current.kind == "string":
            token = self.advance()
            return [("literal", token.line, token.value)]
        if self.current.value == "{":
            return [self.parse_table()]
        raise self.error("expected function arguments")

    def parse_table(self) -> tuple:
        token = self.expect("{")
        fields: list[tuple[tuple, tuple, bool]] = []
        array_index = 1
        while self.current.value != "}":
            if self.match("["):
                key = self.parse_expr()
                self.expect("]")
                self.expect("=")
                value = self.parse_expr()
                is_list = False
            elif self.current.kind == "name" and self.peek(1).value == "=":
                name = self.advance()
                self.expect("=")
                key = ("literal", name.line, name.value)
                value = self.parse_expr()
                is_list = False
            else:
                key = ("literal", self.current.line, array_index)
                value = self.parse_expr()
                array_index += 1
                is_list = True
            fields.append((key, value, is_list))
            if not (self.match(",") or self.match(";")):
                break
        self.expect("}")
        return ("table", token.line, fields)


def parse_source(source: str, filename: str = "<source>") -> list[tuple]:
    return Parser(Lexer(source, filename).lex(), filename).parse()
