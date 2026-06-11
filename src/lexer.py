from src.token import Token, TokenType
from typing import List

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.line = 1
        self.column = 1

    def lex(self) -> List[Token]:
        return [Token(TokenType.EOF, "", self.line, self.column)]
