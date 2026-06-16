from src.lexer import Lexer
from src.token import TokenType

def test_single_characters():
    lexer = Lexer("+ - = ( ) : ,")
    tokens = lexer.lex()
    types = [t.type for t in tokens]
    
    assert TokenType.PLUS in types
    assert TokenType.MINUS in types
    assert TokenType.ASSIGN in types
    assert TokenType.LPAREN in types
    assert TokenType.RPAREN in types
    assert TokenType.COLON in types
    assert TokenType.COMMA in types

def test_keywords_and_identifiers():
    lexer = Lexer("fn let if print my_var")
    tokens = lexer.lex()
    types = [t.type for t in tokens]
    lexemes = [t.lexeme for t in tokens]
    
    assert types[0] == TokenType.FN
    assert types[1] == TokenType.LET
    assert types[2] == TokenType.IF
    assert types[3] == TokenType.PRINT
    assert types[4] == TokenType.IDENTIFIER
    assert lexemes[4] == "my_var"

def test_literals():
    lexer = Lexer('123 45.67 "hello world"')
    tokens = lexer.lex()
    
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].lexeme == "123"
    
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].lexeme == "45.67"
    
    assert tokens[2].type == TokenType.STRING
    assert tokens[2].lexeme == "hello world"

def test_indentation():
    code = """fn main():
    let x = 1
    if x:
        print("yes")
    print("done")
"""
    lexer = Lexer(code)
    tokens = lexer.lex()
    
    # Extract structural tokens
    structs = [t.type for t in tokens if t.type in (TokenType.INDENT, TokenType.DEDENT, TokenType.EOF)]
    
    # We expect:
    # INDENT before `let x = 1`
    # INDENT before `print("yes")`
    # DEDENT before `print("done")`
    # DEDENT at EOF
    # EOF
    assert structs == [TokenType.INDENT, TokenType.INDENT, TokenType.DEDENT, TokenType.DEDENT, TokenType.EOF]

def test_newlines_are_preserved():
    code = "let x = 1\nlet y = 2"
    lexer = Lexer(code)
    tokens = lexer.lex()
    types = [t.type for t in tokens]
    assert TokenType.NEWLINE in types
