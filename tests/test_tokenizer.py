import pytest

from app.lexer.tokenizer import LexicalError, tokenize_arith, tokenize_crud


def test_tokenize_crud_basic():
    code = "CREATE TABLE users(id INT DEFAULT 0, name TEXT);"
    tokens = tokenize_crud(code)
    types = [token.type for token in tokens]
    assert types[:7] == [
        "CREATE",
        "TABLE",
        "IDENT",
        "LPAREN",
        "IDENT",
        "INT",
        "DEFAULT",
    ]


def test_tokenize_arith_expression():
    expr = "a + b * (c - d)"
    tokens = tokenize_arith(expr)
    types = [token.type for token in tokens]
    assert types[:5] == ["ID", "PLUS", "ID", "STAR", "LPAREN"]


def test_tokenize_crud_error():
    with pytest.raises(LexicalError):
        tokenize_crud("CREATE @ TABLE")
