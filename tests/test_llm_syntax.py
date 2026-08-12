import pytest
from src.lexer import Lexer
from src.parser import Parser, ParseError
from src.semantic import SemanticAnalyzer, SemanticError

def test_def_keyword_hint():
    code = "def main():\n    pass"
    tokens = Lexer(code).lex()
    parser = Parser(tokens)
    with pytest.raises(ParseError) as exc_info:
        parser.parse()
    assert "Hint: Use 'fn' for function definitions" in str(exc_info.value)

def test_var_keyword_hint():
    code = "fn main() -> void:\n    var x: int = 5"
    tokens = Lexer(code).lex()
    parser = Parser(tokens)
    with pytest.raises(ParseError) as exc_info:
        parser.parse()
    assert "Hint: Use 'let' or 'let mut' for variable declarations" in str(exc_info.value)

def test_unsafe_hardware_hint():
    code = "fn print_test() -> void:\n    vga_write(0, 0, 65 as u8, 15)"
    tokens = Lexer(code).lex()
    parser = Parser(tokens)
    ast_tree = parser.parse()
    analyzer = SemanticAnalyzer()
    with pytest.raises(SemanticError) as exc_info:
        analyzer.analyze(ast_tree)
    assert "must be inside an @unsafe function" in str(exc_info.value)
