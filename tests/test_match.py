import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator
import llvmlite.binding as llvm

def compile_and_run(source_code: str):
    # Lexing
    lexer = Lexer(source_code)
    tokens = lexer.lex()
    
    # Parsing
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Semantic Analysis
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    
    # Code Generation
    codegen = CodeGenerator()
    codegen.generate_Program(ast)
    llvm_ir = codegen.get_ir()
    
    # JIT Execution
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()
    
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod = llvm.parse_assembly("")
    engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
    
    mod = llvm.parse_assembly(llvm_ir)
    mod.verify()
    engine.add_module(mod)
    engine.finalize_object()
    engine.run_static_constructors()
    
    func_ptr = engine.get_function_address("main")
    
    import ctypes
    cfunc = ctypes.CFUNCTYPE(ctypes.c_int)(func_ptr)
    return cfunc()

def test_match_statement_basic():
    source = """
enum Status { OK, ERROR, PENDING }

fn main() -> int:
    let mut x: int = 10
    let s: Status = Status.ERROR
    
    match s:
        Status.OK =>:
            x = 1
        Status.ERROR =>:
            x = 2
        Status.PENDING =>:
            x = 3
            
    return x
"""
    result = compile_and_run(source)
    assert result == 2

def test_match_statement_wildcard():
    source = """
enum Status { OK, ERROR, PENDING }

fn main() -> int:
    let mut x: int = 0
    let s: Status = Status.PENDING
    
    match s:
        Status.OK =>:
            x = 1
        _ =>:
            x = 99
            
    return x
"""
    result = compile_and_run(source)
    assert result == 99
