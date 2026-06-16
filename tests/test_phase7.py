"""
Phase 7 Tests — Arrays, Enums, Structs, If/While, Return
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer, SemanticError
from src.codegen import CodeGenerator
import src.ast as ast


def lex_parse(source: str) -> ast.Program:
    tokens = Lexer(source).lex()
    return Parser(tokens).parse()


def compile_ok(source: str):
    """Full pipeline: lex → parse → semantic → codegen. Must not raise."""
    tree = lex_parse(source)
    SemanticAnalyzer().analyze(tree)
    cg = CodeGenerator()
    cg.generate(tree)
    return cg.get_ir()


# ==========================================
# Lexer Tests
# ==========================================

class TestLexerPhase7:
    def test_enum_keyword(self):
        from src.token import TokenType
        tokens = Lexer("enum Status { OK, ERROR }").lex()
        types = [t.type for t in tokens]
        assert TokenType.ENUM in types

    def test_semicolon_token(self):
        from src.token import TokenType
        tokens = Lexer("[u8; 16]").lex()
        types = [t.type for t in tokens]
        assert TokenType.SEMICOLON in types

    def test_brace_tokens(self):
        from src.token import TokenType
        tokens = Lexer("{ }").lex()
        types = [t.type for t in tokens]
        assert TokenType.LBRACE in types
        assert TokenType.RBRACE in types

    def test_hex_literal(self):
        from src.token import TokenType
        tokens = Lexer("0xFF").lex()
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(nums) == 1
        assert nums[0].lexeme == "0xFF"

    def test_binary_literal(self):
        from src.token import TokenType
        tokens = Lexer("0b1010").lex()
        nums = [t for t in tokens if t.type == TokenType.NUMBER]
        assert len(nums) == 1
        assert nums[0].lexeme == "0b1010"

    def test_comment_ignored(self):
        from src.token import TokenType
        tokens = Lexer("let x: int = 1 # this is ignored\n").lex()
        # Should have LET, IDENTIFIER, COLON, IDENTIFIER, ASSIGN, NUMBER, NEWLINE, EOF
        lexemes = [t.lexeme for t in tokens if t.type == TokenType.IDENTIFIER]
        assert "x" in lexemes
        # Comment content must not appear
        assert not any("ignored" in t.lexeme for t in tokens)


# ==========================================
# Parser Tests
# ==========================================

class TestParserPhase7:
    def test_enum_declaration(self):
        tree = lex_parse("enum Status { OK, ERROR, PENDING }\n")
        assert len(tree.statements) == 1
        node = tree.statements[0]
        assert isinstance(node, ast.EnumDeclaration)
        assert node.name.name == "Status"
        assert node.variants == ["OK", "ERROR", "PENDING"]

    def test_array_type_annotation(self):
        tree = lex_parse("fn f():\n    let buf: [u8; 4] = [1, 2, 3, 4]\n")
        func = tree.statements[0]
        decl = func.body.statements[0]
        assert decl.type_annotation == "[u8; 4]"

    def test_array_literal_elements(self):
        tree = lex_parse("fn f():\n    let a: [int; 3] = [10, 20, 30]\n")
        decl = tree.statements[0].body.statements[0]
        assert isinstance(decl.initializer, ast.ArrayLiteral)
        assert len(decl.initializer.elements) == 3

    def test_array_index(self):
        tree = lex_parse("fn f():\n    let a: [int; 2] = [1, 2]\n    let x: int = a[0]\n")
        decl = tree.statements[0].body.statements[1]
        assert isinstance(decl.initializer, ast.ArrayIndex)

    def test_struct_literal(self):
        tree = lex_parse(
            "struct Pt:\n    x: int\n    y: int\n"
            "fn f():\n    let p: Pt = Pt { x: 1, y: 2 }\n"
        )
        func_decl = tree.statements[1]
        var_decl  = func_decl.body.statements[0]
        assert isinstance(var_decl.initializer, ast.StructLiteral)
        assert var_decl.initializer.struct_name == "Pt"

    def test_return_statement(self):
        tree = lex_parse("fn add(a: int, b: int) -> int:\n    return a + b\n")
        func = tree.statements[0]
        ret  = func.body.statements[0]
        assert isinstance(ret, ast.ReturnStatement)

    def test_if_elif_else(self):
        src = (
            "fn f(x: int) -> int:\n"
            "    if x == 0:\n"
            "        return 0\n"
            "    elif x < 0:\n"
            "        return 1\n"
            "    else:\n"
            "        return 2\n"
        )
        tree = lex_parse(src)
        func = tree.statements[0]
        stmt = func.body.statements[0]
        assert isinstance(stmt, ast.IfStatement)
        assert len(stmt.elif_branches) == 1
        assert stmt.else_block is not None

    def test_while_statement(self):
        src = (
            "fn f():\n"
            "    let mut i: int = 0\n"
            "    while i < 10:\n"
            "        i = i + 1\n"
        )
        tree = lex_parse(src)
        func = tree.statements[0]
        whl  = func.body.statements[1]
        assert isinstance(whl, ast.WhileStatement)

    def test_bool_literal(self):
        tree = lex_parse("fn f():\n    let t: int = true\n    let ff: int = false\n")
        stmts = tree.statements[0].body.statements
        assert isinstance(stmts[0].initializer, ast.BoolLiteral)
        assert stmts[0].initializer.value is True


# ==========================================
# Semantic Tests
# ==========================================

class TestSemanticPhase7:
    def test_enum_declaration_registers(self):
        src = "enum Color { RED, GREEN, BLUE }\n"
        tree = lex_parse(src)
        sa   = SemanticAnalyzer()
        sa.analyze(tree)
        assert "Color" in sa.enums
        assert sa.enums["Color"] == ["RED", "GREEN", "BLUE"]

    def test_struct_declaration_registers(self):
        src = "struct Point:\n    x: int\n    y: int\n"
        tree = lex_parse(src)
        sa   = SemanticAnalyzer()
        sa.analyze(tree)
        assert "Point" in sa.structs

    def test_array_literal_type_inferred(self):
        src  = "fn f():\n    let a: [int; 3] = [1, 2, 3]\n"
        tree = lex_parse(src)
        sa   = SemanticAnalyzer()
        sa.analyze(tree)  # Must not raise

    def test_array_index_type(self):
        src  = "fn f():\n    let a: [int; 2] = [10, 20]\n    let x: int = a[0]\n"
        tree = lex_parse(src)
        sa   = SemanticAnalyzer()
        sa.analyze(tree)

    def test_if_else_semantic(self):
        src = (
            "fn f(x: int) -> int:\n"
            "    if x == 0:\n"
            "        return 0\n"
            "    else:\n"
            "        return 1\n"
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_while_semantic(self):
        src = (
            "fn f():\n"
            "    let mut i: int = 0\n"
            "    while i < 5:\n"
            "        i = i + 1\n"
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_return_semantic(self):
        src = "fn add(a: int, b: int) -> int:\n    return a + b\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_struct_literal_valid(self):
        src = (
            "struct Pt:\n    x: int\n    y: int\n"
            "fn f():\n    let p: Pt = Pt { x: 1, y: 2 }\n"
        )
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)


# ==========================================
# Codegen (End-to-End) Tests
# ==========================================

class TestCodegenPhase7:
    def test_enum_compiles(self):
        src = "enum Status { OK, ERROR }\nfn main():\n    let s: int = 0\n"
        ir  = compile_ok(src)
        assert "define" in ir

    def test_array_compiles(self):
        src = (
            "fn f():\n"
            "    let buf: [int; 3] = [10, 20, 30]\n"
            "    let x: int = buf[0]\n"
        )
        ir = compile_ok(src)
        assert "alloca" in ir

    def test_struct_compiles(self):
        src = (
            "struct Point:\n    x: int\n    y: int\n"
            "fn f():\n"
            "    let p: Point = Point { x: 5, y: 10 }\n"
            "    let px: int = p.x\n"
        )
        ir = compile_ok(src)
        assert "getelementptr" in ir

    def test_if_else_compiles(self):
        src = (
            "fn f(x: int) -> int:\n"
            "    if x == 0:\n"
            "        return 0\n"
            "    else:\n"
            "        return 1\n"
        )
        ir = compile_ok(src)
        assert "br" in ir

    def test_while_compiles(self):
        src = (
            "fn f():\n"
            "    let mut i: int = 0\n"
            "    while i < 10:\n"
            "        i = i + 1\n"
        )
        ir = compile_ok(src)
        assert "while.cond" in ir

    def test_return_compiles(self):
        src = "fn add(a: int, b: int) -> int:\n    return a + b\n"
        ir  = compile_ok(src)
        assert "ret" in ir

    def test_full_phase7_program(self):
        """The complete test_phase7.os file must compile end-to-end."""
        with open("test_phase7.os", "r") as f:
            src = f.read()
        ir = compile_ok(src)
        assert "define" in ir
