from src.lexer import Lexer
from src.parser import Parser
import src.ast as ast

def parse(source: str) -> ast.Program:
    lexer = Lexer(source)
    tokens = lexer.lex()
    parser = Parser(tokens)
    return parser.parse()

def test_parse_variable_declaration():
    program = parse("let x: int = 5\n")
    assert len(program.statements) == 1
    
    var_decl = program.statements[0]
    assert isinstance(var_decl, ast.VariableDeclaration)
    assert var_decl.name.name == "x"
    assert var_decl.type_annotation == "int"
    assert isinstance(var_decl.initializer, ast.NumberLiteral)
    assert var_decl.initializer.value == 5.0
    assert not var_decl.is_mut
    assert not var_decl.is_shared

def test_parse_shared_mut_variable():
    program = parse("shared let mut y = 10\n")
    var_decl = program.statements[0]
    assert var_decl.name.name == "y"
    assert var_decl.is_mut
    assert var_decl.is_shared
    assert var_decl.type_annotation is None

def test_parse_hwmap():
    source = """
hwmap NetworkHeader:
    mac_dest: u8
    eth_type: u16
"""
    program = parse(source)
    assert len(program.statements) == 1
    
    hwmap_decl = program.statements[0]
    assert isinstance(hwmap_decl, ast.StructDeclaration)
    assert hwmap_decl.name.name == "NetworkHeader"
    assert hwmap_decl.is_hwmap
    assert len(hwmap_decl.fields) == 2
    assert hwmap_decl.fields[0][0].name == "mac_dest"
    assert hwmap_decl.fields[0][1] == "u8"
    assert hwmap_decl.fields[1][0].name == "eth_type"
    assert hwmap_decl.fields[1][1] == "u16"

def test_parse_function_and_lock():
    source = """
fn handle_timer():
    lock system_ticks:
        system_ticks = system_ticks + 1
"""
    program = parse(source)
    fn_decl = program.statements[0]
    assert isinstance(fn_decl, ast.FunctionDeclaration)
    assert fn_decl.name.name == "handle_timer"
    assert len(fn_decl.body.statements) == 1
    
    lock_stmt = fn_decl.body.statements[0]
    assert isinstance(lock_stmt, ast.LockBlock)
    assert lock_stmt.target.name == "system_ticks"
    
    assign_stmt = lock_stmt.body.statements[0]
    assert isinstance(assign_stmt, ast.Assignment)

def test_parse_import():
    program = parse("import std.graphics\n")
    stmt = program.statements[0]
    assert isinstance(stmt, ast.ImportStatement)
    assert stmt.module_name == "std.graphics"

def test_parse_function_call():
    program = parse("hw.inb(96)\n")
    call = program.statements[0]
    assert isinstance(call, ast.FunctionCall)
    assert isinstance(call.callee, ast.MemberAccess)
    assert call.callee.object.name == "hw"
    assert call.callee.property.name == "inb"
    assert len(call.arguments) == 1
    assert call.arguments[0].value == 96.0
