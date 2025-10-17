"""Herramientas para analizar la gramática de expresiones aritméticas.

Incluye:
- Transformación LL(1) de la gramática clásica de expresiones.
- Cálculo de conjuntos FIRST, FOLLOW y tablas de predicción.
- Parser predictivo (descendente) basado en pila.
- Parser CYK para comparación de rendimiento.
- Algoritmo de emparejamiento estilo descenso recursivo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple
import math
import statistics
import time

EPSILON = "ε"
END = "$"


@dataclass(frozen=True)
class Production:
    head: str
    body: Tuple[str, ...]

    def __str__(self) -> str:  # pragma: no cover - representación de apoyo
        rhs = " ".join(self.body) if self.body else EPSILON
        return f"{self.head} → {rhs}"


class Grammar:
    def __init__(self, start_symbol: str, productions: Dict[str, List[Tuple[str, ...]]]):
        self.start_symbol = start_symbol
        self.productions = productions

    def nonterminals(self) -> Set[str]:
        return set(self.productions.keys())

    def terminals(self) -> Set[str]:
        symbols = set()
        for body_list in self.productions.values():
            for body in body_list:
                for symbol in body:
                    if symbol not in self.productions and symbol != EPSILON:
                        symbols.add(symbol)
        return symbols

    def to_production_list(self) -> List[Production]:
        result: List[Production] = []
        for head, bodies in self.productions.items():
            for body in bodies:
                result.append(Production(head, body))
        return result


def expression_grammar_ll1() -> Grammar:
    """Retorna la gramática transformada a LL(1)."""
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
                nullable_prefix = True
                for symbol in body:
                    if symbol not in grammar.productions:  # terminal
                        if symbol not in first[head]:
                            first[head].add(symbol)
                            changed = True
                        nullable_prefix = False
                        break
                    # symbol is nonterminal
                    sym_first = first[symbol]
                    before = len(first[head])
                    first[head].update(sym_first - {EPSILON})
                    if len(first[head]) != before:
                        changed = True
                    if EPSILON not in sym_first:
                        nullable_prefix = False
                        break
                if nullable_prefix:
                    if EPSILON not in first[head]:
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


def predict_sets(grammar: Grammar, first: Dict[str, Set[str]], follow: Dict[str, Set[str]]) -> Dict[Production, Set[str]]:
    predictions: Dict[Production, Set[str]] = {}
    for production in grammar.to_production_list():
        heads_first = set()
        if production.body == (EPSILON,):
            heads_first = follow[production.head]
        else:
            accum: Set[str] = set()
            nullable_prefix = True
            for symbol in production.body:
                if symbol in grammar.productions:
                    accum.update(first[symbol] - {EPSILON})
                    if EPSILON not in first[symbol]:
                        nullable_prefix = False
                        break
                else:
                    accum.add(symbol)
                    nullable_prefix = False
                    break
            if nullable_prefix:
                accum.update(follow[production.head])
            heads_first = accum
        predictions[production] = heads_first
    return predictions


class PredictiveParser:
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.first = compute_first(grammar)
        self.follow = compute_follow(grammar, self.first)
        self.predictions = predict_sets(grammar, self.first, self.follow)
        self.parse_table = self._build_table()

    def _build_table(self) -> Dict[Tuple[str, str], Production]:
        table: Dict[Tuple[str, str], Production] = {}
        for production, tokens in self.predictions.items():
            for token in tokens:
                key = (production.head, token)
                table[key] = production
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

    def parse(self, expr: str) -> List[str]:
        tokens = self.tokenize(expr) + [END]
        stack: List[str] = [END, self.grammar.start_symbol]
        cursor = 0
        actions: List[str] = []
        while stack:
            top = stack.pop()
            current_token = tokens[cursor]
            if top == current_token == END:
                actions.append("Aceptar")
                break
            if top not in self.grammar.productions:  # terminal
                if top == current_token:
                    actions.append(f"Desplazar {top}")
                    cursor += 1
                else:
                    raise ValueError(f"Error de sintaxis: se esperaba {top} y se encontró {current_token}")
                continue
            # top es no terminal
            key = (top, current_token)
            production = self.parse_table.get(key)
            if not production:
                raise ValueError(f"No hay producción para ({top}, {current_token})")
            actions.append(str(production))
            if production.body != (EPSILON,):
                for symbol in reversed(production.body):
                    stack.append(symbol)
        return actions


class CYKParser:
    """Implementación simple del algoritmo CYK."""

    def __init__(self):
        self.grammar = Grammar(
            start_symbol="S",
            productions={
                "S": [("S", "PLUS_PART"), ("S", "TIMES_PART"), ("LP", "GROUP"), ("ID" ,)],
                "PLUS_PART": [("PLUS", "S")],
                "TIMES_PART": [("TIMES", "S")],
                "GROUP": [("S", "RP")],
                "PLUS": [("+",)],
                "TIMES": [("*",)],
                "LP": [("(",)],
                "RP": [(")",)],
                "ID": [("id",)],
            },
        )

    def parse(self, expr: str) -> bool:
        tokens = PredictiveParser(expression_grammar_ll1()).tokenize(expr)
        n = len(tokens)
        if n == 0:
            return False
        table: List[List[Set[str]]] = [[set() for _ in range(n)] for _ in range(n)]
        for i, token in enumerate(tokens):
            for head, bodies in self.grammar.productions.items():
                for body in bodies:
                    if len(body) == 1 and body[0] == token:
                        table[i][i].add(head)
            self._closure(table[i][i])
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                for k in range(i, j):
                    left_cell = table[i][k]
                    right_cell = table[k + 1][j]
                    for head, bodies in self.grammar.productions.items():
                        for body in bodies:
                            if len(body) == 2:
                                b1, b2 = body
                                if b1 in left_cell and b2 in right_cell:
                                    table[i][j].add(head)
                if table[i][j]:
                    self._closure(table[i][j])
        return self.grammar.start_symbol in table[0][n - 1]

    def _closure(self, cell: Set[str]) -> None:
        added = True
        while added:
            added = False
            for head, bodies in self.grammar.productions.items():
                for body in bodies:
                    if len(body) == 1 and body[0] in cell and body[0] in self.grammar.productions:
                        if head not in cell:
                            cell.add(head)
                            added = True


class RecursiveDescentMatcher:
    """Algoritmo de emparejamiento para un parser descendente recursivo."""

    def __init__(self):
        self.tokens: List[str] = []
        self.pos = 0

    def match(self, expr: str) -> bool:
        parser = PredictiveParser(expression_grammar_ll1())
        self.tokens = parser.tokenize(expr)
        self.pos = 0
        result = self._parse_E()
        return result and self.pos == len(self.tokens)

    def _peek(self) -> Optional[str]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _consume(self, token: str) -> bool:
        if self._peek() == token:
            self.pos += 1
            return True
        return False

    def _parse_E(self) -> bool:
        if not self._parse_T():
            return False
        while self._consume("+"):
            if not self._parse_T():
                return False
        return True

    def _parse_T(self) -> bool:
        if not self._parse_F():
            return False
        while self._consume("*"):
            if not self._parse_F():
                return False
        return True

    def _parse_F(self) -> bool:
        token = self._peek()
        if token == "id":
            self.pos += 1
            return True
        if token == "(":
            self.pos += 1
            if not self._parse_E():
                return False
            return self._consume(")")
        return False


@dataclass
class PerformanceResult:
    parser_name: str
    samples: int
    average_ms: float
    stdev_ms: float


def compare_performance(expressions: Iterable[str], repetitions: int = 250) -> List[PerformanceResult]:
    predictive = PredictiveParser(expression_grammar_ll1())
    cyk = CYKParser()
    results: List[PerformanceResult] = []
    for parser_name, parser in ("Predictivo", predictive), ("CYK", cyk):
        timings: List[float] = []
        for expr in expressions:
            start = time.perf_counter()
            for _ in range(repetitions):
                if parser_name == "Predictivo":
                    predictive.parse(expr)
                else:
                    cyk.parse(expr)
            end = time.perf_counter()
            timings.append((end - start) * 1000.0 / repetitions)
        results.append(
            PerformanceResult(
                parser_name=parser_name,
                samples=len(timings),
                average_ms=statistics.mean(timings),
                stdev_ms=statistics.pstdev(timings),
            )
        )
    return results


def describe_sets(parser: PredictiveParser) -> str:
    lines = ["FIRST:"]
    for nt in sorted(parser.first):
        lines.append(f"  {nt}: {sorted(parser.first[nt])}")
    lines.append("FOLLOW:")
    for nt in sorted(parser.follow):
        lines.append(f"  {nt}: {sorted(parser.follow[nt])}")
    lines.append("PREDICT:")
    for production, tokens in parser.predictions.items():
        lines.append(f"  {production}: {sorted(tokens)}")
    return "\n".join(lines)


def _demo():  # pragma: no cover - rutina interactiva
    parser = PredictiveParser(expression_grammar_ll1())
    print(describe_sets(parser))
    sample = "id + id * ( id + id )"
    print("\nTraza del parser predictivo:")
    for action in parser.parse(sample):
        print(f"  {action}")
    cyk = CYKParser()
    print(f"\nCYK acepta '{sample}': {cyk.parse(sample)}")
    matcher = RecursiveDescentMatcher()
    print(f"Descenso recursivo acepta '{sample}': {matcher.match(sample)}")
    print("\nComparativa de rendimiento:")
    expressions = [
        "id + id * id",
        "id * id + id * id + id",
        "id + id + id + id + id + id",
    ]
    for result in compare_performance(expressions, repetitions=200):
        print(f"  {result.parser_name}: media {result.average_ms:.4f} ms, desviación {result.stdev_ms:.4f} ms")


if __name__ == "__main__":
    _demo()
