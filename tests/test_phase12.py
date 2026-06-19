import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def compile_source(source_code: str):
    lexer = Lexer(source_code)
    tokens = lexer.lex()
    parser = Parser(tokens)
    ast_root = parser.parse()
    
    semantic = SemanticAnalyzer()
    semantic.analyze(ast_root)
    
    codegen = CodeGenerator()
    codegen.generate(ast_root)
    return str(codegen.module)

def test_packed_struct():
    source = """
@packed
struct GDTEntry:
    limit_low: u16
    base_low: u16
    base_mid: u8
    access: u8
    granularity: u8
    base_high: u8

fn main() -> int:
    let entry: GDTEntry
    return 0
"""
    ir = compile_source(source)
    assert "<{i16, i16, i8, i8, i8, i8}>" in ir

def test_sizeof_operator():
    source = """
@packed
struct GDTEntry:
    limit_low: u16
    base_low: u16
    base_mid: u8
    access: u8
    granularity: u8
    base_high: u8

fn main() -> int:
    let size: int = sizeof(GDTEntry)
    let size2: int = sizeof(u16)
    return size
"""
    ir = compile_source(source)
    # ptrtoint of GEP over null pointer
    assert "getelementptr <{i16, i16, i8, i8, i8, i8}>, <{i16, i16, i8, i8, i8, i8}>* null, i32 1" in ir
    assert "getelementptr i16, i16* null, i32 1" in ir

def test_packed_hwmap():
    source = """
@packed
hwmap VGA_Char:
    ascii: u8
    color: u8

fn main() -> int:
    let char: VGA_Char
    return 0
"""
    ir = compile_source(source)
    assert "<{i8, i8}>" in ir
