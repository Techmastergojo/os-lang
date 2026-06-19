# OS-Lang Compression Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement extreme compression features into the OS-Lang compiler (Hardware I/O, Pointers/Unsafe, Packed Structs, Pattern Matching, Interrupts) to reduce kernel development boilerplate.

**Architecture:** We are augmenting the existing LLVM-based compiler pipeline. Intrinsics (`inb`, `sizeof`) will be intercepted directly during code generation (in `codegen.py`). New language constructs (`unsafe`, `as`, `@packed`, `@interrupt`, `enum`, `match`) will require updates to `token.py`, `lexer.py`, `ast.py`, `parser.py`, and `codegen.py` to support LLVM translations like `x86_intrcc`, `inttoptr`, packed struct definitions `<{}>`, and jump tables (`switch`).

**Tech Stack:** Python 3, `llvmlite`, `pytest`

---

### Task 1: Hardware I/O Intrinsics

**Files:**
- Modify: `src/codegen.py`
- Test: `tests/test_io_intrinsics.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_io_intrinsics.py
import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.codegen import CodeGen

def test_hardware_io():
    source = "fn test_io() { let port: u16 = 0x60; let val: u8 = inb(port); outw(0x64, 0xFFFF); }"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    codegen = CodeGen()
    codegen.generate(ast)
    ir = str(codegen.module)
    assert "call i8 asm sideeffect" in ir
    assert "in al, dx" in ir
    assert "out dx, ax" in ir
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_io_intrinsics.py -v`
Expected: FAIL with "Undefined function: 'inb'"

- [ ] **Step 3: Write minimal implementation in `codegen.py`**
Modify `generate_FunctionCall` in `src/codegen.py` to intercept I/O intrinsics before the standard function lookup:

```python
# In src/codegen.py -> generate_FunctionCall
        if isinstance(node.callee, ast.Identifier):
            name = node.callee.name
            
            # --- NEW INTERCEPT LOGIC ---
            io_ops = {
                "inb": ("i8", "in al, dx", "=^{al},^{dx},~{dirflag},~{fpsr},~{flags}"),
                "outb": ("void", "out dx, al", "^{dx},^{al},~{dirflag},~{fpsr},~{flags}"),
                "inw": ("i16", "in ax, dx", "=^{ax},^{dx},~{dirflag},~{fpsr},~{flags}"),
                "outw": ("void", "out dx, ax", "^{dx},^{ax},~{dirflag},~{fpsr},~{flags}"),
                "inl": ("i32", "in eax, dx", "=^{eax},^{dx},~{dirflag},~{fpsr},~{flags}"),
                "outl": ("void", "out dx, eax", "^{dx},^{eax},~{dirflag},~{fpsr},~{flags}")
            }
            if name in io_ops:
                ret_type_str, asm_str, constraints = io_ops[name]
                ret_type = ir.VoidType() if ret_type_str == "void" else self.get_llvm_type(ret_type_str)
                args = [self.generate(a) for a in node.arguments]
                func_type = ir.FunctionType(ret_type, [a.type for a in args])
                inline_asm = ir.InlineAsm(func_type, asm_str, constraints, side_effect=True)
                return self.builder.call(inline_asm, args)
            # --- END NEW INTERCEPT LOGIC ---
            
            if name not in self.functions:
                raise Exception(f"Undefined function: '{name}'")
```

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_io_intrinsics.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add tests/test_io_intrinsics.py src/codegen.py
git commit -m "feat: implement hardware port I/O intrinsics via LLVM inline assembly"
```

---

### Task 2: Pointers, Casting (`as`), and `unsafe {}` Block Parsing

**Files:**
- Modify: `src/token.py`, `src/lexer.py`, `src/ast.py`, `src/parser.py`, `src/codegen.py`, `src/semantic.py`
- Test: `tests/test_pointers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pointers.py
import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGen

def test_pointer_cast_and_unsafe():
    source = "fn test() { unsafe { let ptr = 0xB8000 as *mut u16; *ptr = 0x0F41; } }"
    lexer = Lexer(source)
    parser = Parser(lexer.tokenize())
    ast = parser.parse()
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast) # Should pass safely
    
    codegen = CodeGen()
    codegen.generate(ast)
    ir = str(codegen.module)
    assert "inttoptr" in ir
    assert "store i16" in ir
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_pointers.py -v`
Expected: FAIL due to `unsafe` or `as` not being recognized as tokens.

- [ ] **Step 3: Update Tokens & AST (`token.py`, `ast.py`)**

```python
# src/token.py (Add to TokenType enum and KEYWORDS)
    UNSAFE = "UNSAFE"
    AS = "AS"
    STAR = "STAR" # * (if not already present for multiplication)
    AMPERSAND = "AMPERSAND" # &

KEYWORDS = {
    ...
    "unsafe": TokenType.UNSAFE,
    "as": TokenType.AS
}

# src/ast.py (Add new Nodes)
class UnsafeBlock(ASTNode):
    def __init__(self, block):
        self.block = block

class Cast(ASTNode):
    def __init__(self, expression, target_type):
        self.expression = expression
        self.target_type = target_type

class PointerDereference(ASTNode):
    def __init__(self, pointer_expr):
        self.pointer_expr = pointer_expr
```

- [ ] **Step 4: Update Lexer & Parser (`lexer.py`, `parser.py`)**

```python
# src/lexer.py (Add rules for & and *)
# Ensure you capture `*` and `&` as tokens.

# src/parser.py
# In `parse_statement`:
    if self.current_token.type == TokenType.UNSAFE:
        self.eat(TokenType.UNSAFE)
        block = self.parse_block()
        return ast.UnsafeBlock(block)

# In `parse_expression` handling, support `expr as Type`
# Support prefix operators `*` and `&` for PointerDereference and AddressOf.
# Also parse `*mut T` and `*const T` as valid type annotations in `parse_type`.
```

- [ ] **Step 5: Implement Semantic Rules & CodeGen (`semantic.py`, `codegen.py`)**

```python
# src/semantic.py
    def visit_UnsafeBlock(self, node):
        prev = self.in_unsafe
        self.in_unsafe = True
        self.visit(node.block)
        self.in_unsafe = prev

    def visit_PointerDereference(self, node):
        if not getattr(self, 'in_unsafe', False):
            raise Exception("Pointer dereference outside unsafe block!")
        self.visit(node.pointer_expr)

# src/codegen.py
    def generate_Cast(self, node):
        val = self.generate(node.expression)
        target_ll_type = self.get_llvm_type(node.target_type)
        if isinstance(val.type, ir.IntType) and isinstance(target_ll_type, ir.PointerType):
            return self.builder.inttoptr(val, target_ll_type)
        # handle other casts
        return self.builder.bitcast(val, target_ll_type)

    def generate_PointerDereference(self, node):
        ptr = self.generate(node.pointer_expr)
        return self.builder.load(ptr)

    def generate_UnsafeBlock(self, node):
        self.generate(node.block)
```

- [ ] **Step 6: Run test to verify it passes**
Run: `pytest tests/test_pointers.py -v`
Expected: PASS

- [ ] **Step 7: Commit**
```bash
git add src tests
git commit -m "feat: pointer casting, dereferencing, and unsafe blocks"
```

---

### Task 3: Packed Structs & Sizeof

**Files:**
- Modify: `src/parser.py`, `src/codegen.py`
- Test: `tests/test_packed_structs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_packed_structs.py
def test_packed_struct():
    source = "@packed struct Message { a: u8, b: u32 } fn get_size() -> u64 { return sizeof(Message); }"
    # Check that LLVM generates <{ i8, i32 }> and sizeof works
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_packed_structs.py -v`
Expected: FAIL

- [ ] **Step 3: Update Parser (`parser.py`)**

```python
# src/parser.py -> Add check for '@packed' before 'struct'
        is_packed = False
        if self.current_token.type == TokenType.AT and self.peek_token().value == "packed":
            self.eat(TokenType.AT)
            self.eat(TokenType.IDENTIFIER) # "packed"
            is_packed = True
        
        self.eat(TokenType.STRUCT)
        # pass `is_packed` to ast.Struct definition
```

- [ ] **Step 4: Update CodeGen (`codegen.py`)**

```python
# src/codegen.py -> struct creation
        llvm_struct = self.module.context.get_identified_type(node.name)
        # Assuming we can set packed on struct
        llvm_struct.set_body(*field_types)
        llvm_struct.packed = node.is_packed # llvmlite uses 'packed' property

# src/codegen.py -> intercept `sizeof`
        if name == "sizeof":
            type_name = node.arguments[0].name # Simplification
            ll_type = self.get_llvm_type(type_name)
            null_ptr = self.builder.inttoptr(ir.Constant(ir.IntType(64), 0), ll_type.as_pointer())
            size_ptr = self.builder.gep(null_ptr, [ir.Constant(ir.IntType(32), 1)])
            return self.builder.ptrtoint(size_ptr, ir.IntType(64))
```

- [ ] **Step 5: Run test to verify it passes**
Run: `pytest tests/test_packed_structs.py -v`
Expected: PASS

- [ ] **Step 6: Commit**
```bash
git commit -am "feat: support @packed structs and compile-time sizeof intrinsic"
```

---

### Task 4: Enums and Pattern Matching

**Files:**
- Modify: `src/token.py`, `src/parser.py`, `src/codegen.py`
- Test: `tests/test_enums_match.py`

- [ ] **Step 1: Write the failing test**
Create test for `enum Action { Read = 1, Write = 2 }` and a `match` statement.

- [ ] **Step 2: Add `enum` and `match` keywords**
Add to Lexer and AST. Treat `enum` as a list of integer constants assigned to a namespace.

- [ ] **Step 3: Update Parser**
Parse `match value { Case1 => block, Case2 => block, _ => block }`.

- [ ] **Step 4: Update CodeGen (`codegen.py`)**

```python
# src/codegen.py -> generate_Match
        val = self.generate(node.value)
        # default block
        default_block = self.builder.append_basic_block(name="match_default")
        end_block = self.builder.append_basic_block(name="match_end")
        
        switch = self.builder.switch(val, default_block)
        
        for case_node in node.cases:
            case_val = self.generate(case_node.value)
            case_block = self.builder.append_basic_block(name="match_case")
            switch.add_case(case_val, case_block)
            
            self.builder.position_at_end(case_block)
            self.generate(case_node.block)
            self.builder.branch(end_block)
            
        self.builder.position_at_end(default_block)
        if node.default_case:
            self.generate(node.default_case)
        self.builder.branch(end_block)
        
        self.builder.position_at_end(end_block)
```

- [ ] **Step 5: Test and Commit**
Verify `switch` IR is generated. Commit changes.

---

### Task 5: Interrupt Decorators

**Files:**
- Modify: `src/parser.py`, `src/codegen.py`
- Test: `tests/test_interrupts.py`

- [ ] **Step 1: Write failing test**
Create test for `@interrupt fn handler(regs: *mut Registers) { }` verifying the `x86_intrcc` calling convention.

- [ ] **Step 2: Update Parser**
Parse `@interrupt` prefix for function definitions.

- [ ] **Step 3: Update CodeGen (`codegen.py`)**

```python
# src/codegen.py -> generate_Function
        func = ir.Function(self.module, func_type, name=node.name)
        if node.is_interrupt:
            func.calling_convention = 'x86_intrcc'
```

- [ ] **Step 4: Test and Commit**
Run `pytest tests/test_interrupts.py -v`.
`git commit -am "feat: support x86_intrcc via @interrupt decorator"`
