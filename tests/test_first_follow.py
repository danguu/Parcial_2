from app.parsing.first_follow import GrammarAnalyzer
from app.parsing.grammars import arithmetic_ll1


def test_first_follow_arithmetic():
    grammar = arithmetic_ll1()
    analyzer = GrammarAnalyzer(grammar)
    first_e = analyzer.first_sets["E"]
    follow_e = analyzer.follow_sets["E"]
    assert {"LPAREN", "ID"}.issubset(first_e)
    assert "$" in follow_e
    first_tprime = analyzer.first_sets["T'"]
    assert "STAR" in first_tprime and "SLASH" in first_tprime and "ε" in first_tprime
