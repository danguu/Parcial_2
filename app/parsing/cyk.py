"""Conversion to Chomsky Normal Form and CYK parsing."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .grammars import GrammarSpec

Production = Tuple[str, ...]


@dataclass
class CNFGrammar:
    start_symbol: str
    productions: Dict[str, Set[Production]]

    def add_production(self, head: str, body: Production) -> None:
        self.productions.setdefault(head, set()).add(body)

    def heads_for(self, body: Production) -> Set[str]:
        return {head for head, bodies in self.productions.items() if body in bodies}


def power_set(symbols: Sequence[int]) -> Iterable[Set[int]]:
    for r in range(len(symbols) + 1):
        for combo in combinations(symbols, r):
            yield set(combo)


def to_cnf(grammar: GrammarSpec) -> CNFGrammar:
    """Convert a grammar to Chomsky Normal Form."""

    new_start = f"{grammar.start_symbol}_S0"
    productions: Dict[str, Set[Production]] = {head: set(map(tuple, bodies)) for head, bodies in grammar.productions.items()}
    productions[new_start] = {(grammar.start_symbol,)}
    cnf = CNFGrammar(start_symbol=new_start, productions=productions)

    _eliminate_epsilon(cnf)
    _eliminate_units(cnf)
    _eliminate_terminals_in_long_rules(cnf)
    _reduce_long_productions(cnf)
    return cnf


def _eliminate_epsilon(grammar: CNFGrammar) -> None:
    nullable: Set[str] = {head for head, bodies in grammar.productions.items() if () in bodies}
    changed = True
    while changed:
        changed = False
        for head, bodies in grammar.productions.items():
            for body in bodies:
                if body and all(symbol in nullable for symbol in body):
                    if head not in nullable:
                        nullable.add(head)
                        changed = True
    for head, bodies in list(grammar.productions.items()):
        new_bodies: Set[Production] = set()
        for body in list(bodies):
            if body == ():
                continue
            nullable_positions = [i for i, symbol in enumerate(body) if symbol in nullable]
            for subset in power_set(list(range(len(nullable_positions)))):
                indices_to_drop = {nullable_positions[i] for i in subset}
                if indices_to_drop == set(range(len(body))) and head != grammar.start_symbol:
                    continue
                new_body = tuple(symbol for idx, symbol in enumerate(body) if idx not in indices_to_drop)
                if not new_body and head != grammar.start_symbol:
                    continue
                new_bodies.add(new_body if new_body else ())
        bodies.update(new_bodies)
        if head != grammar.start_symbol:
            bodies.discard(())


def _eliminate_units(grammar: CNFGrammar) -> None:
    unit_pairs: Set[Tuple[str, str]] = set()
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 1 and body[0] in grammar.productions:
                unit_pairs.add((head, body[0]))
    changed = True
    while changed:
        changed = False
        for a, b in list(unit_pairs):
            for body in grammar.productions.get(b, set()):
                if len(body) == 1 and body[0] in grammar.productions and (a, body[0]) not in unit_pairs:
                    unit_pairs.add((a, body[0]))
                    changed = True
    for a, b in unit_pairs:
        grammar.productions[a].discard((b,))
        for body in grammar.productions.get(b, set()):
            grammar.productions[a].add(body)


def _eliminate_terminals_in_long_rules(grammar: CNFGrammar) -> None:
    terminals: Set[str] = set()
    for bodies in grammar.productions.values():
        for body in bodies:
            if len(body) > 1:
                for symbol in body:
                    if symbol not in grammar.productions:
                        terminals.add(symbol)
    mapping: Dict[str, str] = {}
    counter = 0
    for terminal in terminals:
        name = f"T_{counter}"
        counter += 1
        grammar.add_production(name, (terminal,))
        mapping[terminal] = name
    for head, bodies in list(grammar.productions.items()):
        updated: Set[Production] = set()
        for body in bodies:
            if len(body) <= 1:
                updated.add(body)
                continue
            new_body = tuple(mapping.get(symbol, symbol) for symbol in body)
            updated.add(new_body)
        grammar.productions[head] = updated


def _reduce_long_productions(grammar: CNFGrammar) -> None:
    counter = 0
    for head, bodies in list(grammar.productions.items()):
        new_bodies: Set[Production] = set()
        for body in bodies:
            if len(body) <= 2:
                new_bodies.add(body)
                continue
            symbols = list(body)
            prev = symbols[0]
            for symbol in symbols[1:-1]:
                new_nt = f"X_{counter}"
                counter += 1
                grammar.add_production(new_nt, (prev, symbol))
                prev = new_nt
            new_bodies.add((prev, symbols[-1]))
        grammar.productions[head] = new_bodies


def cyk_parse(grammar: CNFGrammar, tokens: Sequence[str]) -> Tuple[bool, List[List[Set[str]]]]:
    """Run the CYK algorithm and return whether the string is in the language."""

    if not tokens:
        return (() in grammar.productions.get(grammar.start_symbol, set()), [])
    n = len(tokens)
    table: List[List[Set[str]]] = [[set() for _ in range(n)] for _ in range(n)]
    inverse_index: Dict[str, Set[str]] = {}
    for head, bodies in grammar.productions.items():
        for body in bodies:
            if len(body) == 1 and body[0] not in grammar.productions:
                inverse_index.setdefault(body[0], set()).add(head)
    for i, token in enumerate(tokens):
        table[i][i] = set(inverse_index.get(token, set()))
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            cell: Set[str] = set()
            for k in range(i, j):
                left = table[i][k]
                right = table[k + 1][j]
                for head, bodies in grammar.productions.items():
                    for body in bodies:
                        if len(body) == 2 and body[0] in left and body[1] in right:
                            cell.add(head)
            table[i][j] = cell
    accepted = grammar.start_symbol in table[0][n - 1]
    return accepted, table


def benchmark_vs_ll1(inputs: Sequence[Tuple[str, str]], ll1_parser, tokenizer) -> List[Dict[str, object]]:
    """Compare CYK with an LL(1) parser given input strings."""

    import time
    import tracemalloc

    results: List[Dict[str, object]] = []
    cnf = to_cnf(ll1_parser.grammar)
    for label, text in inputs:
        tokens = tokenizer(text)
        token_types = [token.type for token in tokens]
        tracemalloc.start()
        start = time.perf_counter()
        try:
            ll1_parser.parse(token_types)
            ll1_ok = True
        except Exception:
            ll1_ok = False
        ll1_time = time.perf_counter() - start
        _, ll1_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tracemalloc.start()
        start = time.perf_counter()
        accepted, _ = cyk_parse(cnf, [t for t in token_types if t != "EOF"])
        cyk_time = time.perf_counter() - start
        _, cyk_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        results.append(
            {
                "case": label,
                "input": text,
                "tokens": len(token_types),
                "ll1_time": ll1_time,
                "ll1_peak_mem": ll1_peak,
                "ll1_success": ll1_ok,
                "cyk_time": cyk_time,
                "cyk_peak_mem": cyk_peak,
                "cyk_success": accepted,
            }
        )
    return results
