"""
Phase 8 Tests — C Interoperability (extern "C")
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.token import TokenType
from src.parser import Parser
from src.semantic import SemanticAnalyzer, SemanticError
from src.codegen import CodeGenerator
import src.ast as ast


def lex_parse(source: str) -> ast.Program:
    tokens = Lexer(source).lex()
    return Parser(tokens).parse()


def compile_ok(source: str) -> str:
    """Full pipeline: lex → parse → semantic → codegen. Returns IR string."""
    tree = lex_parse(source)
    SemanticAnalyzer().analyze(tree)
    cg = CodeGenerator()
    cg.generate(tree)
    return cg.get_ir()


# ==========================================
# Lexer Tests
# ==========================================

class TestLexerPhase8:
    def test_extern_keyword(self):
        tokens = Lexer('extern "C" fn malloc(size: int) -> ptr\n').lex()
        types = [t.type for t in tokens]
        assert TokenType.EXTERN in types

    def test_vararg_token(self):
        tokens = Lexer('extern "C" fn printf(fmt: str, ...) -> int\n').lex()
        types = [t.type for t in tokens]
        assert TokenType.VARARG in types

    def test_no_false_vararg(self):
        # Single dot should NOT produce VARARG
        tokens = Lexer("p.x\n").lex()
        types = [t.type for t in tokens]
        assert TokenType.VARARG not in types
        assert TokenType.DOT in types

    def test_extern_abi_string(self):
        tokens = Lexer('extern "C" fn foo()\n').lex()
        strings = [t for t in tokens if t.type == TokenType.STRING]
        assert len(strings) == 1
        assert strings[0].lexeme == "C"


# ==========================================
# Parser Tests
# ==========================================

class TestParserPhase8:
    def test_single_extern_declaration(self):
        src = 'extern "C" fn malloc(size: int) -> ptr\n'
        tree = lex_parse(src)
        node = tree.statements[0]
        assert isinstance(node, ast.ExternDeclaration)
        assert node.name.name == "malloc"
        assert node.abi == "C"
        assert not node.is_variadic
        assert node.return_type == "ptr"

    def test_variadic_extern(self):
        src = 'extern "C" fn printf(fmt: str, ...) -> int\n'
        tree = lex_parse(src)
        node = tree.statements[0]
        assert isinstance(node, ast.ExternDeclaration)
        assert node.name.name == "printf"
        assert node.is_variadic is True

    def test_extern_block(self):
        src = (
            'extern "C":\n'
            '    fn malloc(size: int) -> ptr\n'
            '    fn free(p: ptr)\n'
        )
        tree = lex_parse(src)
        block = tree.statements[0]
        assert isinstance(block, ast.ExternBlock)
        assert block.abi == "C"
        assert len(block.declarations) == 2
        assert block.declarations[0].name.name == "malloc"
        assert block.declarations[1].name.name == "free"

    def test_extern_no_params(self):
        src = 'extern "C" fn abort()\n'
        tree = lex_parse(src)
        node = tree.statements[0]
        assert isinstance(node, ast.ExternDeclaration)
        assert len(node.parameters) == 0
        assert not node.is_variadic

    def test_extern_void_return(self):
        src = 'extern "C" fn exit(code: int)\n'
        tree = lex_parse(src)
        node = tree.statements[0]
        assert node.return_type is None  # No -> means void

    def test_extern_multiple_params(self):
        src = 'extern "C" fn memcpy(dst: ptr, src: ptr, n: int) -> ptr\n'
        tree = lex_parse(src)
        node = tree.statements[0]
        assert len(node.parameters) == 3


# ==========================================
# Semantic Tests
# ==========================================

class TestSemanticPhase8:
    def test_extern_registers_as_callable(self):
        src = 'extern "C" fn puts(s: str) -> int\nfn main():\n    puts("hello")\n'
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)  # Must not raise

    def test_variadic_call_allowed(self):
        src = (
            'extern "C" fn printf(fmt: str, ...) -> int\n'
            'fn main():\n'
            '    printf("val=%d", 42)\n'
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_variadic_call_many_args(self):
        src = (
            'extern "C" fn printf(fmt: str, ...) -> int\n'
            'fn main():\n'
            '    printf("%d %d %d", 1, 2, 3)\n'
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_extern_block_callable(self):
        src = (
            'extern "C":\n'
            '    fn strlen(s: str) -> int\n'
            '    fn puts(s: str) -> int\n'
            'fn main():\n'
            '    let n: int = strlen("hello")\n'
            '    puts("world")\n'
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_extern_undefined_raises(self):
        # Calling a C function without declaring it should error
        src = 'fn main():\n    malloc(64)\n'
        tree = lex_parse(src)
        with pytest.raises(SemanticError, match="not defined"):
            SemanticAnalyzer().analyze(tree)

    def test_extern_wrong_arg_type_raises(self):
        src = (
            'extern "C" fn strlen(s: str) -> int\n'
            'fn main():\n'
            '    strlen(42)\n'  # int instead of str
        )
        tree = lex_parse(src)
        with pytest.raises(SemanticError):
            SemanticAnalyzer().analyze(tree)


# ==========================================
# Codegen (End-to-End) Tests
# ==========================================

class TestCodegenPhase8:
    def test_declare_emitted(self):
        src = 'extern "C" fn malloc(size: int) -> ptr\n'
        ir  = compile_ok(src)
        assert 'declare' in ir
        assert 'malloc' in ir

    def test_variadic_declare(self):
        src = 'extern "C" fn printf(fmt: str, ...) -> int\n'
        ir  = compile_ok(src)
        assert '...' in ir

    def test_extern_block_declares(self):
        src = (
            'extern "C":\n'
            '    fn malloc(size: int) -> ptr\n'
            '    fn free(p: ptr)\n'
        )
        ir = compile_ok(src)
        assert 'malloc' in ir
        assert 'free' in ir

    def test_extern_call_in_function(self):
        src = (
            'extern "C" fn puts(s: str) -> int\n'
            'fn main():\n'
            '    puts("hello")\n'
        )
        ir = compile_ok(src)
        assert 'call' in ir

    def test_full_phase8_program(self):
        """The complete test_phase8.os must compile end-to-end."""
        with open("test_phase8.os", "r") as f:
            src = f.read()
        ir = compile_ok(src)
        # All 10 C functions should be declared
        for fn in ["malloc", "free", "memset", "memcpy", "strlen", "puts",
                   "printf", "abort", "exit", "atoi"]:
            assert fn in ir, f"Expected '{fn}' in IR but not found."
