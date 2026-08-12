import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

def test_web_gui_semantic_layout():
    code = """
guiapp WebDesktop:
    title: "Leopard OS"
    width: 1024
    height: 768

    window Main:
        header TopNav:
            align: center
            justify: space_between
            bg: "#1a1a2e"
            height: 60

            label title_text:
                text: "Kernel Web OS"

        container ContentBody:
            direction: row
            flex: 1

            sidebar LeftPanel:
                width: 200
                bg: "#161625"

                button btn1:
                    text: "Dashboard"

            main AppArea:
                flex: 1
                align: center
                justify: center

                card WelcomeCard:
                    width: 300
                    height: 150

                    label welcome_lbl:
                        text: "Web Layout Success"

        footer BottomBar:
            height: 30
            align: center

            label status:
                text: "Ready"
"""
    tokens = Lexer(code).lex()
    ast_tree = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast_tree)
    codegen = CodeGenerator()
    codegen.generate(ast_tree)
    ir = codegen.get_ir()
    assert "WebDesktop" in ir
    assert "__guielem_" in ir
