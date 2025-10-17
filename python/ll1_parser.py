"""Analizador predictivo LL(1) para la gramática de expresiones."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

EPSILON = "ε"
END = "$"


@dataclass(frozen=True)
class Production:
    head: str
    body: Tuple[str, ...]

    def __str__(self) -> str:
        rhs = " ".join(self.body) if self.body else EPSILON
        return f"{self.head} → {rhs}"


class Grammar:
    """Representa una gramática libre de contexto sencilla."""

    def __init__(self, start_symbol: str, productions: Dict[str, Sequence[Sequence[str]]]):
        self.start_symbol = start_symbol
        self.productions: Dict[str, List[Tuple[str, ...]]] = {
            head: [tuple(body) for body in bodies] for head, bodies in productions.items()
        }

    def nonterminals(self) -> Set[str]:
        return set(self.productions)

    def terminals(self) -> Set[str]:
        terminals: Set[str] = set()
        for bodies in self.productions.values():
            for body in bodies:
                for symbol in body:
                    if symbol not in self.productions and symbol != EPSILON:
                        terminals.add(symbol)
        return terminals

    def iter_productions(self) -> Iterable[Production]:
        for head, bodies in self.productions.items():
            for body in bodies:
                yield Production(head, body)


def expression_grammar_ll1() -> Grammar:
    """Gramática de expresiones transformada a LL(1)."""

    return Grammar(
        start_symbol="E",
        productions={
            "E": [("T", "E'"),],
            "E'": [("+", "T", "E'"), (EPSILON,)],
            "T": [("F", "T'"),],
            "T'": [("*", "F", "T'"), (EPSILON,)],
            "F": [("(", "E", ")"), ("id",)],
        },
    )


def compute_first(grammar: Grammar) -> Dict[str, Set[str]]:
    first: Dict[str, Set[str]] = {nt: set() for nt in grammar.nonterminals()}
    changed = True
    while changed:
        changed = False
        for head, bodies in grammar.productions.items():
            for body in bodies:
                if body == (EPSILON,):
                    if EPSILON not in first[head]:
                        first[head].add(EPSILON)
                        changed = True
                    continue

                nullable = True
                for symbol in body:
                    if symbol in grammar.productions:  # no terminal
                        prev = len(first[head])
                        first[head].update(first[symbol] - {EPSILON})
                        if len(first[head]) != prev:
                            changed = True
                        if EPSILON not in first[symbol]:
                            nullable = False
                            break
                    else:  # terminal
                        if symbol not in first[head]:
                            first[head].add(symbol)
                            changed = True
                        nullable = False
                        break
                if nullable and EPSILON not in first[head]:
                    first[head].add(EPSILON)
                    changed = True
    return first


def compute_follow(grammar: Grammar, first: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
    follow: Dict[str, Set[str]] = {nt: set() for nt in grammar.nonterminals()}
    follow[grammar.start_symbol].add(END)
    changed = True
    while changed:
        changed = False
        for head, bodies in grammar.productions.items():
            for body in bodies:
                trailer = follow[head].copy()
                for symbol in reversed(body):
                    if symbol in grammar.productions:
                        before = len(follow[symbol])
                        follow[symbol].update(trailer)
                        if len(follow[symbol]) != before:
                            changed = True

                        if EPSILON in first[symbol]:
                            trailer = trailer.union(first[symbol] - {EPSILON})
                        else:
                            trailer = first[symbol] - {EPSILON}
                    else:
                        trailer = {symbol}
    return follow


def build_predict_sets(
    grammar: Grammar,
    first: Dict[str, Set[str]],
    follow: Dict[str, Set[str]],
) -> Dict[Production, Set[str]]:
    predict: Dict[Production, Set[str]] = {}
    for production in grammar.iter_productions():
        tokens: Set[str] = set()
        if production.body == (EPSILON,):
            tokens.update(follow[production.head])
        else:
            nullable = True
            for symbol in production.body:
                if symbol in grammar.productions:
                    tokens.update(first[symbol] - {EPSILON})
                    if EPSILON not in first[symbol]:
                        nullable = False
                        break
                else:
                    tokens.add(symbol)
                    nullable = False
                    break
            if nullable:
                tokens.update(follow[production.head])
        predict[production] = tokens
    return predict


class LL1Parser:
    """Parser predictivo sencillo basado en una pila."""

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.first = compute_first(grammar)
        self.follow = compute_follow(grammar, self.first)
        self.predict = build_predict_sets(grammar, self.first, self.follow)
        self.table = self._build_table()

    def _build_table(self) -> Dict[Tuple[str, str], Production]:
        table: Dict[Tuple[str, str], Production] = {}
        for production, tokens in self.predict.items():
            for token in tokens:
                table[(production.head, token)] = production
        return table

    def tokenize(self, expr: str) -> List[str]:
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

    def parse(self, text: str) -> List[str]:
        tokens = self.tokenize(text) + [END]
        stack: List[str] = [END, self.grammar.start_symbol]
        cursor = 0
        steps: List[str] = []

        while stack:
            top = stack.pop()
            current = tokens[cursor]
            if top == current == END:
                steps.append("Aceptar")
                break
            if top not in self.grammar.productions:  # terminal
                if top == current:
                    steps.append(f"Consumir {current}")
                    cursor += 1
                else:
                    raise ValueError(f"Error de sintaxis: se esperaba {top} y llegó {current}")
                continue

            key = (top, current)
            if key not in self.table:
                raise ValueError(f"No hay producción para ({top}, {current})")
            production = self.table[key]
            steps.append(str(production))
            for symbol in reversed(production.body):
                if symbol != EPSILON:
                    stack.append(symbol)

        return steps


def describe_sets(parser: LL1Parser) -> str:
    """Devuelve un resumen legible de FIRST, FOLLOW y tablas de predicción."""

    lines = ["CONJUNTOS FIRST", "----------------"]
    for nt in sorted(parser.first):
        tokens = ", ".join(sorted(parser.first[nt])) or "∅"
        lines.append(f"FIRST({nt}) = {{ {tokens} }}")

    lines.append("\nCONJUNTOS FOLLOW")
    lines.append("-----------------")
    for nt in sorted(parser.follow):
        tokens = ", ".join(sorted(parser.follow[nt])) or "∅"
        lines.append(f"FOLLOW({nt}) = {{ {tokens} }}")

    lines.append("\nPREDICT")
    lines.append("-------")
    for production, tokens in sorted(
        parser.predict.items(), key=lambda item: (item[0].head, item[0].body)
    ):
        joined = ", ".join(sorted(tokens)) or "∅"
        lines.append(f"{production}: {{ {joined} }}")

    return "\n".join(lines)


def _demo() -> None:
    parser = LL1Parser(expression_grammar_ll1())
    sample = "id + id * id"
    print("Expresión de ejemplo:", sample)
    print("Pasos del parser:")
    for step in parser.parse(sample):
        print(" -", step)
    print()
    print(describe_sets(parser))


if __name__ == "__main__":
    _demo()
