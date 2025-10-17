"""Interactive REPL for experimenting with the arithmetic parser."""
from __future__ import annotations

from .lexer.tokenizer import tokenize_arith
from .parsing.ll1_table import LL1Parser
from .parsing.grammars import arithmetic_ll1


def repl() -> None:
    parser = LL1Parser(arithmetic_ll1())
    print("REPL aritmético. Escriba 'exit' para salir.")
    while True:
        try:
            line = input('> ').strip()
        except EOFError:  # pragma: no cover - interactive use
            break
        if line.lower() in {"exit", "quit"}:
            break
        tokens = tokenize_arith(line)
        types = [token.type for token in tokens]
        try:
            parser.parse(types)
            print("Cadena aceptada.")
        except Exception as exc:  # pragma: no cover - feedback for users
            print(f"Error: {exc}")


if __name__ == "__main__":  # pragma: no cover
    repl()
