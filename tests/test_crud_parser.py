import pytest

from app.lexer.tokenizer import tokenize_crud
from app.parsing.grammars import crud_grammar
from app.parsing.ll1_table import LL1ParseError, LL1Parser


def _tokens(text: str):
    return [token.type for token in tokenize_crud(text)]


def test_crud_program_acceptance():
    parser = LL1Parser(crud_grammar())
    text = """
    CREATE TABLE people(id INT, name TEXT);
    READ people WHERE id = 3;
    """.strip()
    parser.parse(_tokens(text))


def test_crud_program_error():
    parser = LL1Parser(crud_grammar())
    with pytest.raises(LL1ParseError):
        parser.parse(_tokens("READ WHERE name = \"Ada\";"))
