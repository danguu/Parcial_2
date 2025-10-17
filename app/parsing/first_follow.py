"""FIRST and FOLLOW set computation for context-free grammars."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence, Set

from .grammars import EPSILON, END_OF_INPUT, GrammarSpec, Production


@dataclass(frozen=True)
class PredictEntry:
    """Associates a production with its PREDICT set."""

    nonterminal: str
    production: Production
    predict: Set[str]


class GrammarAnalyzer:
    """Compute FIRST, FOLLOW, and PREDICT sets for a grammar."""

    def __init__(self, grammar: GrammarSpec) -> None:
        self.grammar = grammar
        self.nonterminals = set(grammar.productions)
        self.terminals = _compute_terminals(grammar.productions, self.nonterminals)
        self.first_sets: Dict[str, Set[str]] = {nt: set() for nt in self.nonterminals}
        self.follow_sets: Dict[str, Set[str]] = {nt: set() for nt in self.nonterminals}
        self.predict_sets: List[PredictEntry] = []
        self._compute()

    def _compute(self) -> None:
        self._compute_first()
        self._compute_follow()
        self._compute_predict()

    def _compute_first(self) -> None:
        changed = True
        while changed:
            changed = False
            for head, prods in self.grammar.productions.items():
                for prod in prods:
                    first_of_prod = self._first_of_sequence(prod)
                    if EPSILON in first_of_prod:
                        if EPSILON not in self.first_sets[head]:
                            self.first_sets[head].add(EPSILON)
                            changed = True
                        first_of_prod.discard(EPSILON)
                    before = len(self.first_sets[head])
                    self.first_sets[head].update(first_of_prod)
                    if len(self.first_sets[head]) != before:
                        changed = True

    def _compute_follow(self) -> None:
        self.follow_sets[self.grammar.start_symbol].add(END_OF_INPUT)
        changed = True
        while changed:
            changed = False
            for head, prods in self.grammar.productions.items():
                for prod in prods:
                    follow_head = self.follow_sets[head]
                    for index, symbol in enumerate(prod):
                        if symbol not in self.nonterminals:
                            continue
                        suffix = prod[index + 1 :]
                        first_suffix = self._first_of_sequence(suffix)
                        before = len(self.follow_sets[symbol])
                        self.follow_sets[symbol].update(first_suffix - {EPSILON})
                        if EPSILON in first_suffix:
                            self.follow_sets[symbol].update(follow_head)
                        if len(self.follow_sets[symbol]) != before:
                            changed = True

    def _compute_predict(self) -> None:
        entries: List[PredictEntry] = []
        for head, prods in self.grammar.productions.items():
            for prod in prods:
                first_set = self._first_of_sequence(prod)
                predict = set(first_set)
                if EPSILON in first_set or not prod:
                    predict.discard(EPSILON)
                    predict.update(self.follow_sets[head])
                entries.append(PredictEntry(head, prod, predict))
        self.predict_sets = entries

    def _first_of_sequence(self, symbols: Sequence[str]) -> Set[str]:
        if not symbols:
            return {EPSILON}
        result: Set[str] = set()
        for symbol in symbols:
            if symbol in self.nonterminals:
                result.update(self.first_sets[symbol] - {EPSILON})
                if EPSILON not in self.first_sets[symbol]:
                    break
            else:
                result.add(symbol)
                break
        else:
            result.add(EPSILON)
        return result

    def as_tables(self) -> Dict[str, Dict[str, Set[str]]]:
        """Return FIRST and FOLLOW tables suitable for inspection."""

        return {
            "FIRST": {nt: set(values) for nt, values in self.first_sets.items()},
            "FOLLOW": {nt: set(values) for nt, values in self.follow_sets.items()},
        }


def _compute_terminals(productions: Mapping[str, Sequence[Production]], nonterminals: Set[str]) -> Set[str]:
    terms: Set[str] = set()
    for prods in productions.values():
        for prod in prods:
            for symbol in prod:
                if symbol not in nonterminals:
                    terms.add(symbol)
    return terms


__all__ = [
    "GrammarAnalyzer",
    "PredictEntry",
]
