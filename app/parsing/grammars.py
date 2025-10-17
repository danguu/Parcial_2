"""Grammar specifications used by the parsing modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

EPSILON: str = "ε"
END_OF_INPUT: str = "$"

Production = Tuple[str, ...]
ProductionMap = Mapping[str, Sequence[Production]]


@dataclass(frozen=True)
class GrammarSpec:
    """Data container describing a context-free grammar."""

    name: str
    start_symbol: str
    productions: Dict[str, List[Production]]

    def nonterminals(self) -> Iterable[str]:
        return self.productions.keys()


def _prod(*symbols: str) -> Production:
    return tuple(symbols)


def arithmetic_ll1() -> GrammarSpec:
    """Return the LL(1) grammar for arithmetic expressions."""

    productions: Dict[str, List[Production]] = {
        "E": [
            _prod("T", "E'"),
        ],
        "E'": [
            _prod("PLUS", "T", "E'"),
            _prod("MINUS", "T", "E'"),
            tuple(),
        ],
        "T": [
            _prod("F", "T'"),
        ],
        "T'": [
            _prod("STAR", "F", "T'"),
            _prod("SLASH", "F", "T'"),
            tuple(),
        ],
        "F": [
            _prod("LPAREN", "E", "RPAREN"),
            _prod("ID"),
        ],
    }
    return GrammarSpec(name="arithmetic_ll1", start_symbol="E", productions=productions)


def arithmetic_original() -> GrammarSpec:
    """Return the original left-recursive arithmetic grammar."""

    productions: Dict[str, List[Production]] = {
        "E": [
            _prod("E", "PLUS", "T"),
            _prod("T"),
        ],
        "T": [
            _prod("T", "STAR", "F"),
            _prod("F"),
        ],
        "F": [
            _prod("LPAREN", "E", "RPAREN"),
            _prod("ID"),
        ],
    }
    return GrammarSpec(name="arithmetic_original", start_symbol="E", productions=productions)


def crud_grammar() -> GrammarSpec:
    """Return the CRUD mini-language grammar."""

    p: Dict[str, List[Production]] = {
        "PROGRAM": [
            _prod("STATEMENT_LIST", "EOF"),
        ],
        "STATEMENT_LIST": [
            _prod("STATEMENT", "SEMICOLON", "STATEMENT_LIST"),
            tuple(),
        ],
        "STATEMENT": [
            _prod("CREATE_STMT"),
            _prod("READ_STMT"),
            _prod("UPDATE_STMT"),
            _prod("DELETE_STMT"),
        ],
        "CREATE_STMT": [
            _prod("CREATE", "TABLE", "IDENT", "LPAREN", "FIELD_LIST", "RPAREN"),
        ],
        "FIELD_LIST": [
            _prod("FIELD_DECL", "FIELD_LIST_TAIL"),
        ],
        "FIELD_LIST_TAIL": [
            _prod("COMMA", "FIELD_DECL", "FIELD_LIST_TAIL"),
            tuple(),
        ],
        "FIELD_DECL": [
            _prod("IDENT", "TYPE_SPEC", "FIELD_DEFAULT"),
        ],
        "TYPE_SPEC": [
            _prod("INT"),
            _prod("TEXT"),
            _prod("BOOL"),
            _prod("FLOAT"),
        ],
        "FIELD_DEFAULT": [
            _prod("DEFAULT", "LITERAL"),
            tuple(),
        ],
        "READ_STMT": [
            _prod("READ", "SOURCE_SPEC", "WHERE_OPTION", "ORDER_OPTION", "LIMIT_OPTION"),
        ],
        "SOURCE_SPEC": [
            _prod("IDENT", "SOURCE_ALIAS"),
        ],
        "SOURCE_ALIAS": [
            _prod("AS", "IDENT"),
            tuple(),
        ],
        "ORDER_OPTION": [
            _prod("ORDER", "BY", "ORDER_LIST"),
            tuple(),
        ],
        "ORDER_LIST": [
            _prod("ORDER_ITEM", "ORDER_LIST_TAIL"),
        ],
        "ORDER_LIST_TAIL": [
            _prod("COMMA", "ORDER_ITEM", "ORDER_LIST_TAIL"),
            tuple(),
        ],
        "ORDER_ITEM": [
            _prod("QUALIFIED_IDENT", "ORDER_DIR"),
        ],
        "ORDER_DIR": [
            _prod("ASC"),
            _prod("DESC"),
            tuple(),
        ],
        "LIMIT_OPTION": [
            _prod("LIMIT", "NUMBER", "LIMIT_TAIL"),
            tuple(),
        ],
        "LIMIT_TAIL": [
            _prod("OFFSET", "NUMBER"),
            tuple(),
        ],
        "UPDATE_STMT": [
            _prod("UPDATE", "IDENT", "SET", "ASSIGNMENT_LIST", "WHERE_OPTION"),
        ],
        "WHERE_OPTION": [
            _prod("WHERE_CLAUSE"),
            tuple(),
        ],
        "ASSIGNMENT_LIST": [
            _prod("ASSIGNMENT", "ASSIGNMENT_LIST_TAIL"),
        ],
        "ASSIGNMENT_LIST_TAIL": [
            _prod("COMMA", "ASSIGNMENT", "ASSIGNMENT_LIST_TAIL"),
            tuple(),
        ],
        "ASSIGNMENT": [
            _prod("QUALIFIED_IDENT", "EQ", "EXPR"),
        ],
        "DELETE_STMT": [
            _prod("DELETE", "FROM", "IDENT", "WHERE_OPTION"),
        ],
        "WHERE_CLAUSE": [
            _prod("WHERE", "DISJUNCTION"),
        ],
        "DISJUNCTION": [
            _prod("CONJUNCTION", "DISJUNCTION_TAIL"),
        ],
        "DISJUNCTION_TAIL": [
            _prod("OR", "CONJUNCTION", "DISJUNCTION_TAIL"),
            tuple(),
        ],
        "CONJUNCTION": [
            _prod("NEGATION", "CONJUNCTION_TAIL"),
        ],
        "CONJUNCTION_TAIL": [
            _prod("AND", "NEGATION", "CONJUNCTION_TAIL"),
            tuple(),
        ],
        "NEGATION": [
            _prod("NOT", "NEGATION"),
            _prod("COMPARISON"),
        ],
        "COMPARISON": [
            _prod("SUM", "COMPARISON_TAIL"),
        ],
        "COMPARISON_TAIL": [
            _prod("REL_OP", "SUM"),
            tuple(),
        ],
        "REL_OP": [
            _prod("EQ"),
            _prod("NEQ"),
            _prod("LT"),
            _prod("LE"),
            _prod("GT"),
            _prod("GE"),
        ],
        "SUM": [
            _prod("TERM", "SUM_TAIL"),
        ],
        "SUM_TAIL": [
            _prod("PLUS", "TERM", "SUM_TAIL"),
            _prod("MINUS", "TERM", "SUM_TAIL"),
            tuple(),
        ],
        "TERM": [
            _prod("FACTOR", "TERM_TAIL"),
        ],
        "TERM_TAIL": [
            _prod("STAR", "FACTOR", "TERM_TAIL"),
            _prod("SLASH", "FACTOR", "TERM_TAIL"),
            tuple(),
        ],
        "FACTOR": [
            _prod("LPAREN", "EXPR", "RPAREN"),
            _prod("QUALIFIED_IDENT"),
            _prod("LITERAL"),
            _prod("MINUS", "FACTOR"),
        ],
        "EXPR": [
            _prod("SUM"),
        ],
        "LITERAL": [
            _prod("NUMBER"),
            _prod("STRING"),
            _prod("BOOLEAN_LITERAL"),
        ],
        "BOOLEAN_LITERAL": [
            _prod("TRUE"),
            _prod("FALSE"),
        ],
        "QUALIFIED_IDENT": [
            _prod("IDENT", "QUALIFIED_IDENT_TAIL"),
        ],
        "QUALIFIED_IDENT_TAIL": [
            _prod("DOT", "IDENT", "QUALIFIED_IDENT_TAIL"),
            tuple(),
        ],
    }
    return GrammarSpec(name="crud", start_symbol="PROGRAM", productions=p)


def epsilon_production() -> Production:
    """Return a reusable epsilon production."""

    return tuple()
