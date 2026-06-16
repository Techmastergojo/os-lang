from dataclasses import dataclass, field
from typing import List, Optional

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    pass

# ==========================================
# Expressions (Produce a value)
# ==========================================

@dataclass
class NumberLiteral(ASTNode):
    value: float  # Stored as float to handle both int/float

@dataclass
class BoolLiteral(ASTNode):
    value: bool

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    operator: str
    right: ASTNode

@dataclass
class FunctionCall(ASTNode):
    callee: ASTNode
    arguments: List[ASTNode]

@dataclass
class MemberAccess(ASTNode):
    object: ASTNode
    property: 'Identifier'

@dataclass
class Cast(ASTNode):
    expr: ASTNode
    target_type: str

@dataclass
class SizeOf(ASTNode):
    target_type: str

# ==========================================
# Phase 7: New Expression Nodes
# ==========================================

@dataclass
class ArrayLiteral(ASTNode):
    """Represents [1, 2, 3] array literal expressions."""
    elements: List[ASTNode]

@dataclass
class ArrayIndex(ASTNode):
    """Represents array[index] element access."""
    array: ASTNode
    index: ASTNode

@dataclass
class StructLiteral(ASTNode):
    """Represents MyStruct { field: value, ... } struct initialization."""
    struct_name: str
    fields: List[tuple]  # List of (field_name: str, value: ASTNode)

@dataclass
class EnumVariant(ASTNode):
    """Represents an enum variant access: Status.OK"""
    enum_name: str
    variant: str

# ==========================================
# Statements (Do not produce a value)
# ==========================================

@dataclass
class VariableDeclaration(ASTNode):
    name: 'Identifier'
    is_mut: bool
    type_annotation: Optional[str]
    initializer: Optional[ASTNode]
    is_shared: bool = False

@dataclass
class Assignment(ASTNode):
    target: ASTNode
    value: ASTNode

@dataclass
class ImportStatement(ASTNode):
    module_name: str

@dataclass
class ReturnStatement(ASTNode):
    value: Optional[ASTNode]

@dataclass
class Block(ASTNode):
    """A collection of statements, e.g., inside an if-statement or function."""
    statements: List[ASTNode]

@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_block: Block
    elif_branches: List[tuple]  # List of (condition, block)
    else_block: Optional[Block]

@dataclass
class WhileStatement(ASTNode):
    condition: ASTNode
    body: Block

@dataclass
class FunctionDeclaration(ASTNode):
    name: 'Identifier'
    parameters: List[tuple]  # List of (name, type)
    return_type: Optional[str]
    body: Block
    # Phase 6: existing decorators
    is_unsafe: bool = False
    is_interrupt: bool = False
    interrupt_number: Optional[int] = None
    # Phase 9: new OS primitive decorators
    is_syscall: bool = False
    syscall_number: Optional[int] = None   # @syscall(0x80)
    is_driver: bool = False                # @driver
    is_noreturn: bool = False              # @noreturn  (panic, halt)
    is_naked: bool = False                 # @naked     (no stack frame)

@dataclass
class StructDeclaration(ASTNode):
    name: 'Identifier'
    fields: List[tuple]  # List of (name, type)
    is_hwmap: bool = False

@dataclass
class EnumDeclaration(ASTNode):
    """Phase 7: enum Status { OK, ERROR, PENDING }"""
    name: 'Identifier'
    variants: List[str]  # List of variant names

@dataclass
class LockBlock(ASTNode):
    """Represents a `lock x:` concurrency block."""
    target: 'Identifier'
    body: Block

@dataclass
class UnsafeBlock(ASTNode):
    """Represents an `@unsafe` block."""
    body: Block

@dataclass
class AsmBlock(ASTNode):
    """Represents an inline assembly block `asm \"...\"`."""
    assembly_string: str

# ==========================================
# Phase 8: C Interoperability Nodes
# ==========================================

@dataclass
class ExternDeclaration(ASTNode):
    """
    A single extern function signature, e.g.:
        extern "C" fn printf(fmt: str, ...) -> int
    """
    name: 'Identifier'
    parameters: List[tuple]   # [(Identifier, type_str), ...]
    return_type: Optional[str]
    is_variadic: bool
    abi: str                  # e.g. "C"

@dataclass
class ExternBlock(ASTNode):
    """
    A block of extern declarations sharing one ABI, e.g.:
        extern "C":
            fn malloc(size: int) -> ptr
            fn free(ptr: ptr)
    """
    abi: str
    declarations: List[ExternDeclaration]

# ==========================================
# Phase 9: OS Primitive Nodes
# ==========================================

@dataclass
class OsIntrinsicCall(ASTNode):
    """
    Built-in OS intrinsics that map directly to single instructions:
        halt()   → hlt
        cli()    → cli
        sti()    → sti
        rdtsc()  → rdtsc  (returns u64 timestamp)
        cpuid(leaf: int) → cpuid (returns struct CpuInfo)
        outb(port: int, val: int)
        inb(port: int) -> int
    """
    name: str                    # e.g. "halt", "cli", "sti", "rdtsc"
    arguments: List[ASTNode]

# ==========================================
# Phase 10: OS Advanced Primitives
# ==========================================

@dataclass
class AsmBlock(ASTNode):
    """
    Inline assembly blocks: asm("mov cr3, {0}", in: ptr)
    """
    assembly_string: str
    args: List[tuple]     # [("in", ASTNode), ("out", ASTNode), ...]

# ==========================================
# Root Node
# ==========================================

@dataclass
class Program(ASTNode):
    """The root of the AST representing an entire source file."""
    statements: List[ASTNode]
