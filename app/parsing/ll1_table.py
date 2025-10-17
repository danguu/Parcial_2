"""LL(1) parsing table construction and predictive parser."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Mapping, MutableMapping, Sequence

from .first_follow import GrammarAnalyzer
from .grammars import END_OF_INPUT, GrammarSpec, Production


class LL1ParseError(Exception):
    """Raised when predictive parsing fails."""

    def __init__(self, expected: Sequence[str], actual: str) -> None:
        expected_str = ", ".join(sorted(expected)) or "<none>"
        super().__init__(f"Expected one of {{{expected_str}}}, got {actual!r}")
        self.expected = list(expected)
        self.actual = actual


@dataclass
class LL1Table:
    """Represent an LL(1) parsing table."""

    table: Dict[str, Dict[str, Production]]

    @classmethod
    def from_grammar(cls, grammar: GrammarSpec) -> "LL1Table":
        analyzer = GrammarAnalyzer(grammar)
        table: Dict[str, Dict[str, Production]] = {
            nt: {} for nt in grammar.productions
        }
        for entry in analyzer.predict_sets:
            for terminal in entry.predict:
                key = "EOF" if terminal == END_OF_INPUT else terminal
                table[entry.nonterminal][key] = entry.production
        return cls(table)


@dataclass
class ParseTrace:
    stack: List[str]
    remaining_input: List[str]
    action: str


class LL1Parser:
    """Predictive parser that uses an LL(1) table."""

    def __init__(self, grammar: GrammarSpec) -> None:
        self.grammar = grammar
        self.table = LL1Table.from_grammar(grammar)

    def parse(self, tokens: Sequence[str]) -> List[ParseTrace]:
        """Parse the provided token sequence and return a trace."""

        stack: List[str] = [END_OF_INPUT, self.grammar.start_symbol]
        position = 0
        trace: List[ParseTrace] = []
        tokens_with_end = list(tokens)
        if not tokens_with_end or tokens_with_end[-1] != "EOF":
            tokens_with_end.append("EOF")
        while stack:
            top = stack.pop()
            current = tokens_with_end[position] if position < len(tokens_with_end) else "EOF"
            trace.append(
                ParseTrace(stack=list(stack), remaining_input=tokens_with_end[position:], action=f"Top={top} Current={current}")
            )
            if top == END_OF_INPUT:
                if current == "EOF":
                    break
                raise LL1ParseError(["EOF"], current)
            if top not in self.table.table:
                if top == current:
                    position += 1
                    continue
                raise LL1ParseError([top], current)
            production = self.table.table[top].get(current)
            if production is None:
                raise LL1ParseError(self.table.table[top].keys(), current)
            if production:
                for symbol in reversed(production):
                    stack.append(symbol)
            else:
                # epsilon production, nothing to push
                pass
        return trace
