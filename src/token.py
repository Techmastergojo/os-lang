from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    LET = auto()
    MUT = auto()
    FN = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    RETURN = auto()
    PRINT = auto()
    IMPORT = auto()
    STRUCT = auto()
    HWMAP = auto()
    SHARED = auto()
    LOCK = auto()
    TRUE = auto()
    FALSE = auto()
    PTR = auto()
    ASM = auto()
    AS = auto()
    SIZEOF = auto()
    ENUM = auto()       # Phase 7: enum keyword
    MATCH = auto()      # Phase 10: match keyword
    SEMICOLON = auto()  # Phase 7: [u8; 16] array syntax
    EXTERN = auto()     # Phase 8: extern "C" declarations
    VARARG = auto()     # Phase 8: variadic ... arguments
    UNSAFE = auto()     # Phase 9: unsafe blocks
    
    # Identifiers and Literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    
    # Operators and Punctuation
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()     # Phase 7: { for enum bodies
    RBRACE = auto()     # Phase 7: } for enum bodies
    COLON = auto()
    COMMA = auto()
    DOT = auto()
    AT = auto()
    ARROW = auto()
    AMPERSAND = auto()
    PIPE = auto()
    CARET = auto()
    LSHIFT = auto()
    RSHIFT = auto()
    FAT_ARROW = auto()  # =>
    
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
