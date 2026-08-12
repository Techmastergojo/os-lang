import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator
from src.main import generate_ai_driver_stub

def test_ai_driver_stub_generation():
    stub_code = generate_ai_driver_stub("RTL8139 NIC")
    assert "init_rtl8139_nic_driver" in stub_code
    assert "@driver" in stub_code
    assert "@interrupt(33)" in stub_code
    
    # Verify generated driver parses and compiles cleanly
    tokens = Lexer(stub_code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "init_rtl8139_nic_driver" in ir

def test_import_c_statement():
    code = 'import_c "pci.h"'
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    # import_c generates no errors
    assert ast_tree is not None
