import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def test_process_declaration_compilation():
    code = """process UserShell:
    entry: shell_main
    stack_size: 4096
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "__process_UserShell" in ir

def test_packet_declaration_compilation():
    code = """packet EthernetHeader:
    dest_mac: u64
    ethertype: u16
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    assert "EthernetHeader" in codegen.struct_types

def test_vfs_mount_compilation():
    code = """vfs RootFS:
    mount "/dev/sda1" as "/" type FAT32
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "__vfs_RootFS" in ir

def test_panic_statement_compilation():
    code = """fn main():
    panic("Kernel panic test")
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "hlt" in ir

def test_guard_decorator_canary():
    code = """@guard
fn protected_func():
    let x: int = 5
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "__stack_canary" in ir
