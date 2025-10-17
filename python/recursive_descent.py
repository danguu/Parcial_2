"""Emparejamiento sencillo mediante descenso recursivo."""
from __future__ import annotations

from typing import List


def _tokenize(expr: str) -> List[str]:
    tokens: List[str] = []
    i = 0
    while i < len(expr):
        char = expr[i]
        if char.isspace():
            i += 1
            continue
        if char in "+*()":
            tokens.append(char)
            i += 1
            continue
        if expr[i : i + 2] == "id":
            tokens.append("id")
            i += 2
            continue
        raise ValueError(f"Símbolo desconocido en posición {i}: {expr[i]!r}")
    return tokens


class RecursiveDescentMatcher:
    def __init__(self, tokens: List[str]):
        self.tokens = tokens
        self.position = 0

    @classmethod
    def from_text(cls, text: str) -> "RecursiveDescentMatcher":
        return cls(_tokenize(text))

    def _peek(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def _consume(self, expected: str) -> bool:
        if self._peek() == expected:
            self.position += 1
            return True
        return False

    def parse(self) -> bool:
        if not self._expr():
            return False
        return self.position == len(self.tokens)

    def _expr(self) -> bool:
        if not self._term():
            return False
        while self._consume("+"):
            if not self._term():
                return False
        return True

    def _term(self) -> bool:
        if not self._factor():
            return False
        while self._consume("*"):
            if not self._factor():
                return False
        return True

    def _factor(self) -> bool:
        if self._consume("id"):
            return True
        if self._consume("("):
            if not self._expr():
                return False
            if not self._consume(")"):
                return False
            return True
        return False


def match(text: str) -> bool:
    return RecursiveDescentMatcher.from_text(text).parse()


if __name__ == "__main__":
    expression = "id * ( id + id )"
    print(expression, "->", match(expression))
