import pytest

from app.lexer.tokenizer import tokenize_arith
from app.parsing.grammars import arithmetic_ll1
from app.parsing.ll1_table import LL1ParseError, LL1Parser
from app.parsing.shift_reduce import SLRParser
from app.parsing.cyk import cyk_parse, to_cnf
from app.parsing.recursive_descent import RecursiveDescentMatcher


def tokens_from(text: str):
    return [token.type for token in tokenize_arith(text)]


def test_ll1_accepts_expression():
    parser = LL1Parser(arithmetic_ll1())
    parser.parse(tokens_from("a + b * c"))


def test_ll1_rejects_incomplete_expression():
    parser = LL1Parser(arithmetic_ll1())
    with pytest.raises(LL1ParseError):
        parser.parse(tokens_from("a +"))


def test_slr_trace_contains_accept():
    parser = SLRParser(arithmetic_ll1())
    trace = parser.parse(tokens_from("a * (b + c)"))
    assert any("accept" in step for _, _, step in trace)


def test_cyk_matches_arithmetic():
    cnf = to_cnf(arithmetic_ll1())
    accepted, _ = cyk_parse(cnf, [t for t in tokens_from("a + b") if t != "EOF"])
    assert accepted


def test_recursive_descent_trace():
    matcher = RecursiveDescentMatcher(arithmetic_ll1())
    success, trace = matcher.match(tokens_from("a * b"))
    assert success
    assert trace
