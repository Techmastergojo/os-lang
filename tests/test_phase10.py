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
    return codegen.module

def test_hwmap_declaration():
    source = """
hwmap NetworkHeader:
    mac_dest: [u8; 6]
    mac_src:  [u8; 6]
    eth_type: u16

fn main() -> int:
    let mut header: NetworkHeader
    return 0

"""
    module = compile_source(source)
    ir = str(module)
    assert "<{[6 x i8], [6 x i8], i16}>" in ir

def test_asm_block():
    source = """
@unsafe
fn switch_page_directory(dir_ptr: ptr[u32]):
    asm("mov cr3, $0", in: dir_ptr)
"""
    module = compile_source(source)
    ir = str(module)
    assert "call void asm sideeffect \"mov cr3, $0\", \"r,~{memory},~{dirflag},~{fpsr},~{flags}\"" in ir

def test_asm_block_out():
    source = """
@unsafe
fn get_cr3() -> ptr[u32]:
    let mut cr3_val: ptr[u32] = 0
    cr3_val = asm("mov $0, cr3", out: cr3_val)
    return cr3_val
"""
    module = compile_source(source)
    ir = str(module)
    assert "call i64 asm sideeffect \"mov $0, cr3\", \"=r,~{memory},~{dirflag},~{fpsr},~{flags}\"" in ir

def test_asm_block_fails_outside_unsafe():
    source = """
fn switch_page_directory(dir_ptr: ptr[u32]):
    asm("mov cr3, $0", in: dir_ptr)
"""
    with pytest.raises(Exception, match="must be inside an @unsafe"):
        compile_source(source)
