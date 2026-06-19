import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def test_pointer_cast_and_unsafe():
    source = """
fn test():
    unsafe:
        let p: *mut u16 = 0xB8000 as *mut u16
        *p = 0x0F41 as u16
"""
    lexer = Lexer(source)
    parser = Parser(lexer.lex())
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast) # Should pass safely
    
    codegen = CodeGenerator()
    codegen.generate(ast)
    ir = codegen.get_ir()
    assert "inttoptr" in ir
    assert "store i16" in ir
