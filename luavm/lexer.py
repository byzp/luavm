from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional


class CompileError(Exception):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    value: Any
    line: int
    column: int


KEYWORDS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}

MULTI_SYMBOLS = ("...", "==", "~=", "<=", ">=", "..")


class Lexer:
    def __init__(self, source: str, filename: str = "<source>") -> None:
        self.source = source[1:] if source.startswith("\ufeff") else source
        self.filename = filename
        self.i = 0
        self.line = 1
        self.column = 1
        self.tokens: list[Token] = []

    def error(self, message: str) -> CompileError:
        return CompileError(f"{self.filename}:{self.line}:{self.column}: {message}")

    def advance(self, count: int = 1) -> str:
        out = self.source[self.i : self.i + count]
        for ch in out:
            if ch == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        self.i += count
        return out

    def peek(self, count: int = 1) -> str:
        return self.source[self.i : self.i + count]

    def lex(self) -> list[Token]:
        while self.i < len(self.source):
            ch = self.peek()
            if ch in " \t\r\n\f\v":
                self.advance()
                continue
            if self.peek(2) == "--":
                self.skip_comment()
                continue
            line, column = self.line, self.column
            if ch in "'\"":
                self.tokens.append(Token("string", self.read_string(), line, column))
                continue
            long_level = self.long_bracket_level()
            if long_level is not None:
                self.tokens.append(
                    Token("string", self.read_long_string(long_level), line, column)
                )
                continue
            if ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ch == "_":
                value = self.read_name()
                kind = "keyword" if value in KEYWORDS else "name"
                self.tokens.append(Token(kind, value, line, column))
                continue
            if ("0" <= ch <= "9") or (
                ch == "." and self.peek(2)[1:2] and "0" <= self.peek(2)[1:2] <= "9"
            ):
                self.tokens.append(Token("number", self.read_number(), line, column))
                continue
            matched = next(
                (
                    symbol
                    for symbol in MULTI_SYMBOLS
                    if self.peek(len(symbol)) == symbol
                ),
                None,
            )
            if matched is not None:
                self.advance(len(matched))
                self.tokens.append(Token("symbol", matched, line, column))
                continue
            if ch in "{}[](),;:+-*/%^#=<>.":
                self.advance()
                self.tokens.append(Token("symbol", ch, line, column))
                continue
            raise self.error(f"unexpected character {ch!r}")
        self.tokens.append(Token("eof", "<eof>", self.line, self.column))
        return self.tokens

    def skip_comment(self) -> None:
        self.advance(2)
        long_level = self.long_bracket_level()
        if long_level is not None:
            opening_length = long_level + 2
            self.advance(opening_length)
            closing = "]" + ("=" * long_level) + "]"
            end = self.source.find(closing, self.i)
            if end < 0:
                raise self.error("unterminated long comment")
            self.advance(end - self.i + len(closing))
            return
        while self.i < len(self.source) and self.peek() not in "\r\n":
            self.advance()

    def long_bracket_level(self) -> Optional[int]:
        if self.peek() != "[":
            return None
        cursor = self.i + 1
        while cursor < len(self.source) and self.source[cursor] == "=":
            cursor += 1
        if cursor < len(self.source) and self.source[cursor] == "[":
            return cursor - self.i - 1
        return None

    def read_name(self) -> str:
        start = self.i
        while self.i < len(self.source):
            ch = self.peek()
            if not (
                ("A" <= ch <= "Z")
                or ("a" <= ch <= "z")
                or ("0" <= ch <= "9")
                or ch == "_"
            ):
                break
            self.advance()
        return self.source[start : self.i]

    def read_number(self) -> Any:
        rest = self.source[self.i :]
        match = re.match(
            r"(?:0[xX][0-9a-fA-F]+|(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+)(?:[eE][+-]?[0-9]+)?)",
            rest,
        )
        if not match:
            raise self.error("malformed number")
        text = match.group(0)
        if text.endswith(".") and self.source[self.i + len(text) :].startswith("."):
            raise self.error("malformed number")
        self.advance(len(text))
        try:
            if text.lower().startswith("0x"):
                return int(text, 16)
            value = float(text)
            if value.is_integer() and "." not in text and "e" not in text.lower():
                return int(value)
            return value
        except ValueError as exc:
            raise self.error(f"malformed number {text!r}") from exc

    def read_long_string(self, level: int) -> str:
        opening_length = level + 2
        self.advance(opening_length)
        closing = "]" + ("=" * level) + "]"
        end = self.source.find(closing, self.i)
        if end < 0:
            raise self.error("unterminated long string")
        text = self.source[self.i : end]
        self.advance(end - self.i + len(closing))
        if text.startswith("\r\n"):
            text = text[2:]
        elif text.startswith("\n"):
            text = text[1:]
        return text

    def read_string(self) -> str:
        quote = self.advance()
        out: list[str] = []
        while self.i < len(self.source):
            ch = self.advance()
            if ch == quote:
                return "".join(out)
            if ch == "\n" or ch == "\r":
                raise self.error("newline in short string")
            if ch != "\\":
                out.append(ch)
                continue
            if self.i >= len(self.source):
                raise self.error("unterminated escape")
            esc = self.advance()
            escapes = {
                "a": "\a",
                "b": "\b",
                "f": "\f",
                "n": "\n",
                "r": "\r",
                "t": "\t",
                "v": "\v",
                "\\": "\\",
                '"': '"',
                "'": "'",
            }
            if esc in escapes:
                out.append(escapes[esc])
            elif esc == "\n":
                out.append("\n")
            elif esc == "\r":
                if self.peek() == "\n":
                    self.advance()
                out.append("\n")
            elif esc == "z":
                while self.i < len(self.source) and self.peek() in " \t\r\n\f\v":
                    self.advance()
            elif "0" <= esc <= "9":
                digits = esc
                while (
                    len(digits) < 3
                    and self.i < len(self.source)
                    and "0" <= self.peek() <= "9"
                ):
                    digits += self.advance()
                value = int(digits, 10)
                if value > 255:
                    raise self.error("decimal escape exceeds 255")
                out.append(chr(value))
            else:
                out.append(esc)
        raise self.error("unterminated string")
