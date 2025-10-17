"""Tokenization utilities for CRUD and arithmetic grammars."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, List, Sequence


@dataclass(frozen=True)
class Token:
    """Represents a lexical token with positional metadata."""

    type: str
    value: str
    line: int
    column: int

    def __repr__(self) -> str:  # pragma: no cover - helper for debugging
        return f"Token(type={self.type!r}, value={self.value!r}, line={self.line}, column={self.column})"


class LexicalError(Exception):
    """Raised when tokenization fails."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"{message} (line {line}, column {column})")
        self.line = line
        self.column = column


CRUD_KEYWORDS = {
    "CREATE",
    "TABLE",
    "DEFAULT",
    "READ",
    "AS",
    "ORDER",
    "BY",
    "ASC",
    "DESC",
    "LIMIT",
    "OFFSET",
    "UPDATE",
    "SET",
    "DELETE",
    "FROM",
    "WHERE",
    "AND",
    "OR",
    "NOT",
    "TRUE",
    "FALSE",
    "INT",
    "TEXT",
    "BOOL",
    "FLOAT",
}

CRUD_SYMBOLS = {
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
    ".": "DOT",
    ";": "SEMICOLON",
}

CRUD_OPERATORS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "=": "EQ",
    "!": None,  # part of !=
    "<": "LT",
    ">": "GT",
}

CRUD_TWO_CHAR = {
    "!=": "NEQ",
    "<=": "LE",
    ">=": "GE",
}

ARITH_OPERATORS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    "(": "LPAREN",
    ")": "RPAREN",
}


def _consume_identifier(source: str, start: int) -> int:
    idx = start
    while idx < len(source) and (source[idx].isalnum() or source[idx] == "_"):
        idx += 1
    return idx


def _consume_number(source: str, start: int) -> int:
    idx = start
    while idx < len(source) and source[idx].isdigit():
        idx += 1
    if idx < len(source) and source[idx] == ".":
        idx += 1
        while idx < len(source) and source[idx].isdigit():
            idx += 1
    return idx


def _consume_string(source: str, start: int) -> int:
    idx = start + 1
    escaped = False
    while idx < len(source):
        ch = source[idx]
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            return idx + 1
        idx += 1
    raise LexicalError("Unterminated string literal", _line_of(source, start), _column_of(source, start))


def _line_of(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _column_of(source: str, offset: int) -> int:
    last_newline = source.rfind("\n", 0, offset)
    if last_newline == -1:
        return offset + 1
    return offset - last_newline


def tokenize_crud(source: str) -> List[Token]:
    """Tokenize the CRUD mini-language."""

    tokens: List[Token] = []
    idx = 0
    while idx < len(source):
        ch = source[idx]
        if ch in " \t\r\n":
            idx += 1
            continue
        if ch == "#":
            idx = source.find("\n", idx)
            if idx == -1:
                break
            continue
        line = _line_of(source, idx)
        column = _column_of(source, idx)
        if ch.isalpha() or ch == "_":
            end = _consume_identifier(source, idx)
            value = source[idx:end]
            token_type = value.upper() if value.upper() in CRUD_KEYWORDS else "IDENT"
            tokens.append(Token(token_type, value, line, column))
            idx = end
            continue
        if ch.isdigit():
            end = _consume_number(source, idx)
            value = source[idx:end]
            tokens.append(Token("NUMBER", value, line, column))
            idx = end
            continue
        if ch == '"':
            end = _consume_string(source, idx)
            value = source[idx:end]
            tokens.append(Token("STRING", value, line, column))
            idx = end
            continue
        two_char = source[idx : idx + 2]
        if two_char in CRUD_TWO_CHAR:
            tokens.append(Token(CRUD_TWO_CHAR[two_char], two_char, line, column))
            idx += 2
            continue
        if ch in CRUD_OPERATORS and CRUD_OPERATORS[ch]:
            tokens.append(Token(CRUD_OPERATORS[ch], ch, line, column))
            idx += 1
            continue
        if ch == "!" and source[idx : idx + 2] != "!=":
            raise LexicalError("Unexpected '!'", line, column)
        if ch in CRUD_SYMBOLS:
            tokens.append(Token(CRUD_SYMBOLS[ch], ch, line, column))
            idx += 1
            continue
        raise LexicalError(f"Unexpected character {ch!r}", line, column)
    tokens.append(Token("EOF", "", _line_of(source, len(source)), 1))
    return tokens


def tokenize_arith(source: str) -> List[Token]:
    """Tokenize arithmetic expressions with identifiers."""

    tokens: List[Token] = []
    idx = 0
    while idx < len(source):
        ch = source[idx]
        if ch in " \t\r\n":
            idx += 1
            continue
        line = _line_of(source, idx)
        column = _column_of(source, idx)
        if ch.isalpha() or ch == "_":
            end = _consume_identifier(source, idx)
            value = source[idx:end]
            tokens.append(Token("ID", value, line, column))
            idx = end
            continue
        if ch.isdigit():
            end = _consume_number(source, idx)
            value = source[idx:end]
            tokens.append(Token("ID", value, line, column))
            idx = end
            continue
        if ch in ARITH_OPERATORS:
            tokens.append(Token(ARITH_OPERATORS[ch], ch, line, column))
            idx += 1
            continue
        raise LexicalError(f"Unexpected character {ch!r}", line, column)
    tokens.append(Token("EOF", "", _line_of(source, len(source)), 1))
    return tokens


def iter_types(tokens: Sequence[Token]) -> Iterator[str]:
    """Yield token types only."""

    for token in tokens:
        yield token.type


def strip_values(tokens: Iterable[Token]) -> List[str]:
    """Return a list of token types excluding EOF value when used for parsing traces."""

    types: List[str] = []
    for token in tokens:
        types.append(token.type)
    return types
