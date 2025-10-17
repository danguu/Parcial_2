import pathlib
import sys

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from cyk_parser import CYKParser, compare_with_ll1
from ll1_parser import LL1Parser, describe_sets, expression_grammar_ll1
from recursive_descent import match


def test_first_sets_contains_expected_tokens():
    parser = LL1Parser(expression_grammar_ll1())
    first_e = parser.first["E"]
    assert "id" in first_e
    assert "(" in first_e


def test_follow_sets_for_e_prime_contains_end_marker():
    parser = LL1Parser(expression_grammar_ll1())
    assert "$" in parser.follow["E'"], "E' debe poder finalizar en fin de cadena"


def test_predictive_parser_accepts_valid_expression():
    parser = LL1Parser(expression_grammar_ll1())
    actions = parser.parse("id + id * id")
    assert actions[-1] == "Aceptar"


def test_predictive_parser_rejects_invalid_expression():
    parser = LL1Parser(expression_grammar_ll1())
    try:
        parser.parse("id + * id")
    except ValueError as exc:
        message = str(exc)
        assert "Error de sintaxis" in message or "No hay producción" in message
    else:
        raise AssertionError("Se esperaba ValueError")


def test_describe_sets_returns_text():
    parser = LL1Parser(expression_grammar_ll1())
    summary = describe_sets(parser)
    assert "FIRST(E)" in summary
    assert "FOLLOW(E')" in summary


def test_cyk_parser_matches_same_language():
    cyk = CYKParser()
    assert cyk.parse("id + id * id")
    assert not cyk.parse("id + + id")


def test_recursive_descent_matcher():
    assert match("id * ( id + id )")
    assert not match("id * ( id + )")


def test_performance_results_have_positive_times():
    results = compare_with_ll1(["id + id"], repetitions=2)
    assert len(results) == 1
    name, ll1_time, cyk_time = results[0]
    assert name == "id + id"
    assert ll1_time >= 0.0
    assert cyk_time >= 0.0
