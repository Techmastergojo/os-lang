import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def generate_ir(source: str) -> str:
    lexer = Lexer(source)
    parser = Parser(lexer.lex())
    program = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)
    
    codegen = CodeGenerator()
    codegen.generate(program)
    
    return codegen.get_ir()

def test_codegen_basic_function():
    source = """
fn add(a: int, b: int) -> int:
    let mut result = a + b
"""
    ir_code = generate_ir(source)
    
    assert 'define i64 @"add"(i64 %"a", i64 %"b")' in ir_code
    assert "add i64" in ir_code
    assert "ret i64 0" in ir_code # Implicit return fallback

def test_codegen_interrupt_calling_convention():
    source = """
@interrupt(32)
fn handle_timer():
    let x = 1
"""
    ir_code = generate_ir(source)
    
    # Check if x86_intrcc calling convention is applied
    assert 'x86_intrcc void @"handle_timer"()' in ir_code
