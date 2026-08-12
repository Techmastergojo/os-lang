import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def test_compile_concise_keyboard_driver():
    code = """
@interrupt(33)
fn keyboard_handler():
    let key: int = inb(0x60)
    vga_write(0, 0, key as u8, 15)
    outb(0x20, 0x20)
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "keyboard_handler" in ir
    assert "753664" in ir  # 0xB8000 VGA buffer address

def test_compile_concise_cursor_driver():
    code = """
@unsafe
fn update_cursor(x: int, y: int):
    draw_cursor(x, y, 14)
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "update_cursor" in ir
    assert "219" in ir  # block cursor character

def test_compile_concise_pixel_driver():
    code = """
@unsafe
fn render_pixel(x: int, y: int):
    draw_pixel(x, y, 0x00FF00)
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "render_pixel" in ir
    assert "4244635648" in ir  # 0xFD000000 LFB base address
