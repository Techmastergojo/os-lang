import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator
from src.token import Token, TokenType

class TestPhase11Multitasking(unittest.TestCase):

    def compile_source(self, source: str) -> str:
        lexer = Lexer(source)
        tokens = lexer.lex()
        parser = Parser(tokens)
        ast_root = parser.parse()
        semantic = SemanticAnalyzer()
        semantic.analyze(ast_root)
        codegen = CodeGenerator()
        codegen.generate(ast_root)
        return codegen.get_ir()

    def test_naked_function(self):
        source = """
@naked
fn context_switch():
    asm("pusha")
    asm("popa")
    asm("iret")
        """
        ir_code = self.compile_source(source)
        # Verify the LLVM 'naked' attribute is present on the function
        self.assertIn("naked", ir_code)
        self.assertIn("@\"context_switch\"", ir_code)

    def test_volatile_memory(self):
        source = """
@unsafe
fn write_hw_reg(p: ptr[u64], val: u64):
    volatile_store(p, val)

@unsafe
fn read_hw_reg(p: ptr[u64]) -> u64:
    return volatile_load(p)
        """
        ir_code = self.compile_source(source)
        # Volatile load and store translate to inline assembly
        self.assertIn("mov $1, $0", ir_code)

    def test_atomic_operations(self):
        source = """
@unsafe
fn spinlock_acquire(lck: ptr[u64]):
    let old_val: u64 = atomic_xchg(lck, 1)
    let prev: u64 = atomic_cmpxchg(lck, 0, 1)
    let x: u64 = atomic_add(lck, 1)
    let y: u64 = atomic_sub(lck, 1)
        """
        ir_code = self.compile_source(source)
        self.assertIn("atomicrmw xchg", ir_code)
        self.assertIn("cmpxchg", ir_code)
        self.assertIn("atomicrmw add", ir_code)
        self.assertIn("atomicrmw sub", ir_code)
        self.assertIn("seq_cst seq_cst", ir_code)

    def test_task_structure(self):
        source = """
hwmap TaskState:
    eax: u32
    ebx: u32
    ecx: u32
    edx: u32
    esi: u32
    edi: u32
    ebp: u32
    esp: u32
    eip: u32
    eflags: u32
    cr3: u32

@unsafe
fn init_task(task_p: ptr[TaskState]):
    let mut a: u32 = 0
        """
        ir_code = self.compile_source(source)
        # Verify that packed struct is generated successfully
        self.assertIn("<{i32, i32, i32, i32, i32, i32, i32, i32, i32, i32, i32}>*", ir_code)

if __name__ == "__main__":
    unittest.main()
