import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def test_hardware_io():
    source = """
@unsafe
fn test_io():
    let port: u16 = 0x60
    let val: u8 = inb(port)
    outw(0x64, 0xFFFF)
"""
    lexer = Lexer(source)
    parser = Parser(lexer.lex())
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    codegen = CodeGenerator()
    codegen.generate(ast)
    ir = codegen.get_ir()
    assert 'call i8 asm sideeffect "inb %dx,%al"' in ir
    assert 'call void asm sideeffect "outw %ax,%dx"' in ir
