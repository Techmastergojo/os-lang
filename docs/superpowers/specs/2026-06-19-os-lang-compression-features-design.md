# Design Specification: OS-Lang Extreme Compression Features

## Purpose
Introduce 5 major compiler-level features to drastically reduce the boilerplate required for bare-metal OS development, enabling millions of lines of OS code to be compressed into thousands.

## 1. Hardware Port I/O (Intrinsics)
**Description:** Native translation of port read/write operations without external C/Assembly functions.
**Implementation:**
- The Code Generator (`codegen.py`) intercepts `inb`, `outb`, `inw`, `outw`, `inl`, and `outl` function calls.
- It generates LLVM inline assembly (e.g., `in al, dx`, `out dx, al`) directly.
- **Scope:** Handled entirely in CodeGen without expanding the AST.

## 2. Pointers, Casting, and Safety
**Description:** Ability to cast raw integers to memory addresses and manipulate them, wrapped in a strict safety scope.
**Implementation:**
- **Parser (`parser.py`):** Add the `as` keyword for casting, `unsafe { ... }` blocks, pointer arithmetic (`ptr + offset`), and dereferencing (`*ptr`).
- **CodeGen (`codegen.py`):** Translate `as *mut T` to LLVM's `inttoptr` instruction.
- **Semantic Analyzer (`semantic.py`):** Enforce that any pointer dereferencing or casting occurs *strictly* within an `unsafe {}` block, ensuring no accidental memory corruption.

## 3. Packed Structs & Sizeof
**Description:** Dense memory layouts for IPC (Inter-Process Communication) binary messaging.
**Implementation:**
- Add `@packed` decorator to the struct parser.
- **CodeGen:** Translates to LLVM packed structs `<{ ... }>` instead of standard `{ ... }`, eliminating padding bytes automatically.
- Add a `sizeof(Type)` compiler intrinsic that leverages LLVM's `getelementptr` (GEP) to calculate exact byte sizes with zero runtime cost.

## 4. Enums and Pattern Matching
**Description:** Clean syntax for message types with O(1) branch performance.
**Implementation:**
- Add `enum` parsing (acts as grouped integer constants).
- Add `match` statement parser.
- **CodeGen:** Compile `match` blocks directly into LLVM `switch` instructions, which LLVM optimizes into fast assembly jump tables.

## 5. Interrupt Decorators
**Description:** Eliminate manual assembly boilerplate for hardware interrupt handlers.
**Implementation:**
- Add `@interrupt` decorator for functions.
- **CodeGen:** Tag the generated LLVM function with the `x86_intrcc` calling convention.
- LLVM will natively emit instructions to push registers, set up the stack frame, map the frame to function parameters, and return using `iret`.
