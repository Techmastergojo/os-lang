from src.token import Token, TokenType
from typing import List

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.line = 1
        self.column = 1
        self.current = 0

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        if self.is_at_end():
            return '\0'
        c = self.source[self.current]
        self.current += 1
        if c == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return c

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def lex(self) -> List[Token]:
        tokens = []
        while not self.is_at_end():
            start_col = self.column
            c = self.advance()
            
            if c in [' ', '\t', '\r', '\n']:
                continue
            
            token_type = None
            if c == '+': token_type = TokenType.PLUS
            elif c == '-': token_type = TokenType.MINUS
            elif c == '=': token_type = TokenType.ASSIGN
            elif c == '(': token_type = TokenType.LPAREN
            elif c == ')': token_type = TokenType.RPAREN
            elif c == ':': token_type = TokenType.COLON
            elif c == ',': token_type = TokenType.COMMA
            
            if token_type is not None:
                tokens.append(Token(token_type, c, self.line, start_col))
            else:
                pass # Unhandled characters for now

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens
