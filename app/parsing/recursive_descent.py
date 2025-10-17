"""Recursive descent matching with memoization for demonstration purposes."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from .grammars import GrammarSpec, Production, arithmetic_ll1


@dataclass
class MatchTrace:
    nonterminal: str
    production: Production
    start_index: int
    end_index: Optional[int]
    success: bool


class RecursiveDescentMatcher:
    """Recursive descent matcher with memoization to avoid exponential blow-up."""

    def __init__(self, grammar: GrammarSpec | None = None) -> None:
        self.grammar = grammar or arithmetic_ll1()
        self.trace: List[MatchTrace] = []

    def match(self, tokens: Sequence[str]) -> Tuple[bool, List[MatchTrace]]:
        """Attempt to match the entire token sequence and return trace information."""

        token_list = list(tokens)
        if not token_list or token_list[-1] != "EOF":
            token_list.append("EOF")
        self.trace.clear()
        success, position = self._match_nonterminal(self.grammar.start_symbol, 0, tuple(token_list))
        accepted = success and position is not None and position == len(token_list) - 1
        return accepted, list(self.trace)

    def _record(self, nonterminal: str, production: Production, start: int, end: Optional[int], success: bool) -> None:
        self.trace.append(MatchTrace(nonterminal, production, start, end, success))

    def _match_nonterminal(self, nonterminal: str, position: int, tokens: Tuple[str, ...]) -> Tuple[bool, Optional[int]]:
        for production in self.grammar.productions[nonterminal]:
            success, end_pos = self._match_production(nonterminal, production, position, tokens)
            self._record(nonterminal, production, position, end_pos, success)
            if success:
                return True, end_pos
        return False, None

    @lru_cache(maxsize=None)
    def _match_symbol(self, symbol: str, position: int, tokens: Tuple[str, ...]) -> Tuple[bool, Optional[int]]:
        if position >= len(tokens):
            return False, None
        if symbol in self.grammar.productions:
            return self._match_nonterminal(symbol, position, tokens)
        current = tokens[position]
        if current == symbol:
            return True, position + 1
        return False, None

    def _match_production(
        self, nonterminal: str, production: Production, position: int, tokens: Tuple[str, ...]
    ) -> Tuple[bool, Optional[int]]:
        if not production:
            return True, position
        current_pos = position
        for symbol in production:
            if symbol in self.grammar.productions:
                success, next_pos = self._match_symbol(symbol, current_pos, tokens)
            else:
                success, next_pos = (current_pos < len(tokens) and tokens[current_pos] == symbol, current_pos + 1 if current_pos < len(tokens) else None)
            if not success or next_pos is None:
                return False, None
            current_pos = next_pos
        return True, current_pos


__all__ = ["RecursiveDescentMatcher", "MatchTrace"]
