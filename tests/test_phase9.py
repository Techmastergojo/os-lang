"""
Phase 9 Tests — OS Primitives
@syscall, @driver, @noreturn, @naked decorators
OS intrinsics: halt, cli, sti, rdtsc, cpuid, outb, inb
Built-in structs: InterruptFrame, CpuState
Hardware constants: PORT_*, IRQ_*
"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer, SemanticError
from src.codegen import CodeGenerator
import src.ast as ast


def lex_parse(src: str) -> ast.Program:
    return Parser(Lexer(src).lex()).parse()

def compile_ok(src: str) -> str:
    tree = lex_parse(src)
    SemanticAnalyzer().analyze(tree)
    cg = CodeGenerator()
    cg.generate(tree)
    return cg.get_ir()


# ==========================================
# Parser Tests
# ==========================================

class TestParserPhase9:
    def test_syscall_decorator(self):
        src = "@syscall(1)\nfn sys_write(fd: int, buf: ptr, n: int) -> int:\n    return 0\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert isinstance(fn, ast.FunctionDeclaration)
        assert fn.is_syscall is True
        assert fn.syscall_number == 1
        assert fn.name.name == "sys_write"

    def test_driver_decorator(self):
        src = "@driver\nfn uart_init():\n    return\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert fn.is_driver is True
        assert fn.is_unsafe is True

    def test_noreturn_decorator(self):
        src = "@noreturn\nfn panic():\n    halt()\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert fn.is_noreturn is True

    def test_naked_decorator(self):
        src = "@naked\nfn _start():\n    halt()\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert fn.is_naked is True
        assert fn.is_unsafe is True

    def test_syscall_zero(self):
        src = "@syscall(0)\nfn sys_read(fd: int, buf: ptr, n: int) -> int:\n    return 0\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert fn.syscall_number == 0

    def test_interrupt_no_ptr_param_ok(self):
        src = "@interrupt(32)\nfn timer_handler():\n    halt()\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        assert fn.is_interrupt is True
        assert fn.interrupt_number == 32

    def test_os_intrinsic_halt(self):
        src = "@noreturn\nfn panic():\n    cli()\n    halt()\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        stmts = fn.body.statements
        assert any(isinstance(s, ast.OsIntrinsicCall) and s.name == "cli" for s in stmts)
        assert any(isinstance(s, ast.OsIntrinsicCall) and s.name == "halt" for s in stmts)

    def test_os_intrinsic_outb(self):
        src = "@unsafe\nfn init():\n    outb(0x20, 0x11)\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        call = fn.body.statements[0]
        assert isinstance(call, ast.OsIntrinsicCall)
        assert call.name == "outb"
        assert len(call.arguments) == 2

    def test_os_intrinsic_rdtsc(self):
        src = "@unsafe\nfn timing():\n    let t: int = rdtsc()\n"
        tree = lex_parse(src)
        fn = tree.statements[0]
        decl = fn.body.statements[0]
        assert isinstance(decl, ast.VariableDeclaration)
        assert isinstance(decl.initializer, ast.OsIntrinsicCall)
        assert decl.initializer.name == "rdtsc"


# ==========================================
# Semantic Tests
# ==========================================

class TestSemanticPhase9:
    def test_noreturn_void_ok(self):
        src = "@noreturn\nfn panic():\n    halt()\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)  # must not raise

    def test_noreturn_nonvoid_raises(self):
        src = "@noreturn\nfn bad() -> int:\n    return 0\n"
        tree = lex_parse(src)
        with pytest.raises(SemanticError, match="void return type"):
            SemanticAnalyzer().analyze(tree)

    def test_syscall_implies_unsafe(self):
        # outb inside @syscall should be allowed (syscall implies unsafe)
        src = "@syscall(1)\nfn sys_write(fd: int, n: int) -> int:\n    outb(0x3F8, 65)\n    return n\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_driver_implies_unsafe(self):
        src = "@driver\nfn pic_init():\n    outb(0x20, 0x11)\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_outb_requires_unsafe(self):
        src = "fn safe_fn():\n    outb(0x20, 0x11)\n"
        tree = lex_parse(src)
        with pytest.raises(SemanticError, match="unsafe"):
            SemanticAnalyzer().analyze(tree)

    def test_halt_cli_sti_no_unsafe_needed(self):
        # halt/cli/sti are safe (no memory ops)
        src = "@noreturn\nfn panic():\n    cli()\n    sti()\n    halt()\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_rdtsc_no_unsafe_needed(self):
        src = "fn get_time() -> int:\n    return rdtsc()\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)

    def test_interrupt_ptr_param_raises(self):
        src = "@interrupt(32)\nfn timer(frame: ptr):\n    halt()\n"
        tree = lex_parse(src)
        with pytest.raises(SemanticError, match="cannot be a ptr"):
            SemanticAnalyzer().analyze(tree)

    def test_builtin_interrupt_frame_struct(self):
        # InterruptFrame should be pre-registered as a struct
        sa = SemanticAnalyzer()
        assert "InterruptFrame" in sa.structs
        assert "ip" in sa.structs["InterruptFrame"]
        assert "flags" in sa.structs["InterruptFrame"]

    def test_builtin_cpu_state_struct(self):
        sa = SemanticAnalyzer()
        assert "CpuState" in sa.structs
        assert "rax" in sa.structs["CpuState"]

    def test_hardware_constants_defined(self):
        sa = SemanticAnalyzer()
        # Check PORT and IRQ constants exist
        assert sa.current_scope.resolve("PORT_PIC1_CMD") is not None
        assert sa.current_scope.resolve("IRQ_KEYBOARD") is not None

    def test_intrinsic_arg_count_error(self):
        src = "@unsafe\nfn bad():\n    outb(0x20)\n"  # missing second arg
        tree = lex_parse(src)
        with pytest.raises(SemanticError, match="expects 2 arg"):
            SemanticAnalyzer().analyze(tree)

    def test_numeric_widths_compatible(self):
        # u8/u16/u64 should assign to int without error
        src = "@unsafe\nfn demo():\n    let b: int = inb(0x60)\n    let t: int = rdtsc()\n"
        tree = lex_parse(src)
        SemanticAnalyzer().analyze(tree)


# ==========================================
# Codegen Tests
# ==========================================

class TestCodegenPhase9:
    def test_noreturn_attribute_in_ir(self):
        src = "@noreturn\nfn panic():\n    cli()\n    halt()\n"
        ir = compile_ok(src)
        assert "noreturn" in ir

    def test_naked_attribute_in_ir(self):
        src = "@naked\nfn _start():\n    halt()\n"
        ir = compile_ok(src)
        assert "naked" in ir

    def test_syscall_linkage_external(self):
        src = "@syscall(1)\nfn sys_write(fd: int) -> int:\n    return 0\n"
        ir = compile_ok(src)
        assert "define" in ir
        # llvmlite quotes function names: @"sys_write"
        assert '"sys_write"' in ir
        # @syscall sets external linkage
        assert "external" in ir

    def test_halt_emits_hlt_asm(self):
        src = "@noreturn\nfn panic():\n    halt()\n"
        ir = compile_ok(src)
        assert "hlt" in ir

    def test_cli_emits_cli_asm(self):
        src = "@noreturn\nfn panic():\n    cli()\n    halt()\n"
        ir = compile_ok(src)
        assert "cli" in ir

    def test_rdtsc_emits_rdtsc_asm(self):
        src = "fn get_time() -> int:\n    return rdtsc()\n"
        ir = compile_ok(src)
        assert "rdtsc" in ir

    def test_outb_emits_outb_asm(self):
        src = "@driver\nfn pic_init():\n    outb(0x20, 0x11)\n"
        ir = compile_ok(src)
        assert "outb" in ir

    def test_inb_emits_inb_asm(self):
        src = "@driver\nfn kbd_read():\n    let key: int = inb(0x60)\n"
        ir = compile_ok(src)
        assert "inb" in ir

    def test_interrupt_handler_cc(self):
        src = "@interrupt(32)\nfn timer_handler():\n    halt()\n"
        ir = compile_ok(src)
        assert "x86_intrcc" in ir

    def test_noreturn_unreachable_terminator(self):
        src = "@noreturn\nfn panic():\n    cli()\n    halt()\n"
        ir = compile_ok(src)
        assert "unreachable" in ir

    def test_full_phase9_program(self):
        with open("test_phase9.os") as f:
            src = f.read()
        ir = compile_ok(src)
        # 'external' linkage (@syscall), 'weak_odr' (@driver), noreturn, naked,
        # x86_intrcc CC, all intrinsic asm instructions, unreachable terminator
        for feature in ["external", "weak_odr", "noreturn", "naked", "x86_intrcc",
                         "hlt", "cli", "sti", "rdtsc", "outb", "inb",
                         "unreachable"]:
            assert feature in ir, f"Expected '{feature}' in IR"
