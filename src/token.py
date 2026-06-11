from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    LET = auto()
    FN = auto()
    IF = auto()
    PRINT = auto()
    
    # Identifiers and Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Operators and Punctuation
    PLUS = auto()
    MINUS = auto()
    ASSIGN = auto()
    LPAREN = auto()
    RPAREN = auto()
    COLON = auto()
    COMMA = auto()
    
    # Structure
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
