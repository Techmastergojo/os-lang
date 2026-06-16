import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer, SemanticError

def analyze(source: str):
    lexer = Lexer(source)
    parser = Parser(lexer.lex())
    program = parser.parse()
    analyzer = SemanticAnalyzer()
    analyzer.analyze(program)

def test_semantic_valid_assignment():
    analyze("let mut x: int = 5\nx = 10\n")

def test_semantic_immutable_error():
    with pytest.raises(SemanticError, match="Cannot reassign to immutable variable"):
        analyze("let x = 5\nx = 10\n")

def test_semantic_type_mismatch_decl():
    with pytest.raises(SemanticError, match="Type mismatch"):
        analyze('let mut x: int = "hello"\n')

def test_semantic_type_mismatch_assign():
    with pytest.raises(SemanticError, match="Type mismatch"):
        analyze('let mut x = 5\nx = "hello"\n')
        
def test_semantic_undefined_variable():
    with pytest.raises(SemanticError, match="Variable 'y' is not defined."):
        analyze("let mut x = 5\nx = y + 5\n")

def test_semantic_scope():
    source = """
fn do_something():
    let x = 5
let y = x
"""
    with pytest.raises(SemanticError, match="Variable 'x' is not defined."):
        analyze(source)

def test_semantic_shared_lock_enforcement():
    source = """
shared let mut counter: int = 0
fn increment():
    counter = counter + 1
"""
    with pytest.raises(SemanticError, match="Concurrency error: Shared variable 'counter' accessed outside a lock block."):
        analyze(source)

def test_semantic_shared_lock_valid():
    source = """
shared let mut counter: int = 0
fn increment():
    lock counter:
        counter = counter + 1
"""
    analyze(source)

def test_semantic_pointer_safety():
    source = """
fn do_stuff():
    let mut p: ptr[u8] = 0
    p = 1
"""
    with pytest.raises(SemanticError, match="Memory safety: Pointer 'p' accessed outside @unsafe."):
        analyze(source)

def test_semantic_pointer_unsafe_valid():
    source = """
@unsafe
fn do_stuff():
    let mut p: ptr[u8] = 0
    p = 1
"""
    analyze(source)

def test_semantic_function_call_args():
    source = """
fn add(a: int, b: int) -> int:
    let x = a + b
fn main():
    add(5, "hello")
"""
    with pytest.raises(SemanticError, match="Argument 2 to 'add': expected 'int', got 'str'."):
        analyze(source)

def test_semantic_function_call_arg_count():
    source = """
fn add(a: int, b: int) -> int:
    let x = a + b
fn main():
    add(5)
"""
    with pytest.raises(SemanticError, match="Function 'add' expects 2 args, got 1."):
        analyze(source)

def test_semantic_struct_access():
    source = """
struct Point:
    x: int
    y: int
fn main():
    let mut pt: Point = 0
    pt.z = 10
"""
    with pytest.raises(SemanticError, match="Struct 'Point' has no field 'z'."):
        analyze(source)

def test_semantic_struct_valid():
    source = """
struct Point:
    x: int
    y: int
fn main():
    let mut pt: Point = 0
    let a: int = pt.x
"""
    analyze(source)
