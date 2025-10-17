"""Shift-reduce parser (SLR) for the arithmetic grammar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Set, Tuple

from .first_follow import GrammarAnalyzer
from .grammars import END_OF_INPUT, GrammarSpec, Production, arithmetic_ll1

Symbol = str


@dataclass(frozen=True)
class LR0Item:
    head: str
    production: Production
    dot: int

    def next_symbol(self) -> str | None:
        if self.dot < len(self.production):
            return self.production[self.dot]
        return None

    def advance(self) -> "LR0Item":
        return LR0Item(self.head, self.production, self.dot + 1)

    def is_complete(self) -> bool:
        return self.dot >= len(self.production)


State = frozenset[LR0Item]


def closure(items: Iterable[LR0Item], grammar: GrammarSpec) -> State:
    """Compute the closure of a set of LR(0) items."""

    nonterminals = set(grammar.productions)
    result: Set[LR0Item] = set(items)
    changed = True
    while changed:
        changed = False
        for item in list(result):
            symbol = item.next_symbol()
            if symbol and symbol in nonterminals:
                for production in grammar.productions[symbol]:
                    new_item = LR0Item(symbol, production, 0)
                    if new_item not in result:
                        result.add(new_item)
                        changed = True
    return frozenset(result)


def goto(state: State, symbol: str, grammar: GrammarSpec) -> State:
    advanced = [item.advance() for item in state if item.next_symbol() == symbol]
    if not advanced:
        return frozenset()
    return closure(advanced, grammar)


@dataclass
class Action:
    kind: str
    value: int | Tuple[str, Production] | None

    def __str__(self) -> str:  # pragma: no cover - debugging helper
        if self.kind == "shift":
            return f"shift {self.value}"
        if self.kind == "reduce":
            head, prod = self.value  # type: ignore[assignment]
            rhs = " ".join(prod) if prod else "ε"
            return f"reduce {head} -> {rhs}"
        return self.kind


class SLRParser:
    """Basic SLR(1) parser for the arithmetic grammar."""

    def __init__(self, grammar: GrammarSpec | None = None) -> None:
        self.grammar = grammar or arithmetic_ll1()
        self.augmented_start = f"{self.grammar.start_symbol}_start"
        augmented_productions = dict(self.grammar.productions)
        augmented_productions[self.augmented_start] = [(self.grammar.start_symbol,)]
        self.augmented = GrammarSpec(
            name=f"{self.grammar.name}_augmented",
            start_symbol=self.augmented_start,
            productions=augmented_productions,
        )
        self.states, self.action_table, self.goto_table = self._build_tables()

    def _build_tables(self) -> Tuple[List[State], Dict[Tuple[int, str], Action], Dict[Tuple[int, str], int]]:
        analyzer = GrammarAnalyzer(self.grammar)
        follow_sets = analyzer.follow_sets
        states: List[State] = []
        state_index: Dict[State, int] = {}
        transitions: Dict[Tuple[int, str], int] = {}
        action_table: Dict[Tuple[int, str], Action] = {}
        goto_table: Dict[Tuple[int, str], int] = {}

        start_state = closure([LR0Item(self.augmented_start, (self.grammar.start_symbol,), 0)], self.augmented)
        states.append(start_state)
        state_index[start_state] = 0
        queue = [0]
        while queue:
            idx = queue.pop(0)
            state = states[idx]
            symbols = set(item.next_symbol() for item in state if item.next_symbol() is not None)
            for symbol in symbols:
                next_state = goto(state, symbol, self.augmented)
                if not next_state:
                    continue
                if next_state not in state_index:
                    state_index[next_state] = len(states)
                    states.append(next_state)
                    queue.append(state_index[next_state])
                target_index = state_index[next_state]
                transitions[(idx, symbol)] = target_index
        # build action table
        for i, state in enumerate(states):
            for item in state:
                next_sym = item.next_symbol()
                if next_sym is None:
                    if item.head == self.augmented_start:
                        action_table[(i, "EOF")] = Action("accept", None)
                    else:
                        follow = follow_sets[item.head]
                        for terminal in follow:
                            terminal_name = "EOF" if terminal == END_OF_INPUT else terminal
                            action_table[(i, terminal_name)] = Action("reduce", (item.head, item.production))
                elif next_sym in self.grammar.productions:
                    target = transitions.get((i, next_sym))
                    if target is not None:
                        goto_table[(i, next_sym)] = target
                else:
                    target = transitions.get((i, next_sym))
                    if target is not None:
                        action_table[(i, next_sym)] = Action("shift", target)
        return states, action_table, goto_table

    goto_table: Dict[Tuple[int, str], int]

    def parse(self, tokens: Sequence[str]) -> List[Tuple[List[int], List[str], str]]:
        """Parse tokens and return a trace of configurations."""

        input_tokens = list(tokens)
        if not input_tokens or input_tokens[-1] != "EOF":
            input_tokens.append("EOF")
        stack: List[int] = [0]
        position = 0
        trace: List[Tuple[List[int], List[str], str]] = []
        while True:
            state = stack[-1]
            current = input_tokens[position]
            action = self.action_table.get((state, current))
            trace.append((list(stack), input_tokens[position:], str(action) if action else "error"))
            if action is None:
                raise ValueError(f"Unexpected token {current!r} in state {state}")
            if action.kind == "shift":
                stack.append(action.value)  # type: ignore[arg-type]
                position += 1
            elif action.kind == "reduce":
                head, production = action.value  # type: ignore[assignment]
                for _ in production:
                    stack.pop()
                goto_state = self.goto_table.get((stack[-1], head))
                if goto_state is None:
                    raise ValueError(f"No goto for ({stack[-1]}, {head})")
                stack.append(goto_state)
            elif action.kind == "accept":
                break
        return trace
