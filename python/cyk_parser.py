"""Implementación sencilla del algoritmo CYK para la gramática de expresiones."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

Token = str


def _tokenize(expr: str) -> List[Token]:
    tokens: List[Token] = []
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


@dataclass
class CYKGrammar:
    start: str
    binary: Dict[str, Set[Tuple[str, str]]]
    unary: Dict[str, Set[str]]
    terminals: Dict[str, Set[str]]

    def nonterminals(self) -> Set[str]:
        nts = set(self.binary.keys()) | set(self.unary.keys()) | set(self.terminals.keys())
        return nts


def expression_grammar_for_cyk() -> CYKGrammar:
    """Versión simplificada en forma casi-CNF para el algoritmo CYK."""

    return CYKGrammar(
        start="S",
        binary={
            "S": {("T", "S1")},
            "S1": {("PLUS", "X1")},
            "X1": {("T", "S1")},
            "T": {("F", "T1")},
            "T1": {("TIMES", "X2")},
            "X2": {("F", "T1")},
            "F": {("LPAREN", "X3")},
            "X3": {("S", "RPAREN")},
        },
        unary={
            "S": {"T"},
            "S1": {"PLUS_T"},
            "X1": {"T"},
            "T": {"F"},
            "T1": {"TIMES_F"},
            "X2": {"F"},
        },
        terminals={
            "PLUS": {"+"},
            "PLUS_T": {"+"},
            "TIMES": {"*"},
            "TIMES_F": {"*"},
            "LPAREN": {"("},
            "RPAREN": {")"},
            "F": {"id"},
        },
    )


def _closure(cell: Set[str], unary: Dict[str, Set[str]]) -> Set[str]:
    """Cierra transitivamente las producciones unarias A -> B."""

    changed = True
    result = set(cell)
    while changed:
        changed = False
        for head, bodies in unary.items():
            for symbol in bodies:
                if symbol in result and head not in result:
                    result.add(head)
                    changed = True
    return result


class CYKParser:
    def __init__(self, grammar: CYKGrammar | None = None):
        self.grammar = grammar or expression_grammar_for_cyk()

    def parse(self, text: str) -> bool:
        tokens = _tokenize(text)
        n = len(tokens)
        if n == 0:
            return False

        table: List[List[Set[str]]] = [[set() for _ in range(n)] for _ in range(n)]

        # Inicializar con producciones terminales
        for i, token in enumerate(tokens):
            for head, terminals in self.grammar.terminals.items():
                if token in terminals:
                    table[i][i].add(head)
            table[i][i] = _closure(table[i][i], self.grammar.unary)

        # Algoritmo principal
        for span in range(2, n + 1):
            for start in range(n - span + 1):
                end = start + span - 1
                cell: Set[str] = set()
                for partition in range(start, end):
                    left = table[start][partition]
                    right = table[partition + 1][end]
                    for head, pairs in self.grammar.binary.items():
                        for left_symbol, right_symbol in pairs:
                            if left_symbol in left and right_symbol in right:
                                cell.add(head)
                table[start][end] = _closure(cell, self.grammar.unary)

        return self.grammar.start in table[0][n - 1]


def compare_with_ll1(samples: Sequence[str], repetitions: int = 5) -> List[Tuple[str, float, float]]:
    """Mide el tiempo promedio (ms) del parser predictivo vs. CYK."""

    from time import perf_counter

    from ll1_parser import LL1Parser, expression_grammar_ll1

    ll1 = LL1Parser(expression_grammar_ll1())
    cyk = CYKParser()

    def _time(fn) -> float:
        start = perf_counter()
        fn()
        end = perf_counter()
        return (end - start) * 1000

    results: List[Tuple[str, float, float]] = []
    for sample in samples:
        ll1_times = [_time(lambda s=sample: ll1.parse(s)) for _ in range(repetitions)]
        cyk_times = [_time(lambda s=sample: cyk.parse(s)) for _ in range(repetitions)]
        results.append((sample, sum(ll1_times) / repetitions, sum(cyk_times) / repetitions))
    return results


if __name__ == "__main__":
    parser = CYKParser()
    expr = "id + id * id"
    print("Expresión:", expr)
    print("¿Pertenece?", parser.parse(expr))
