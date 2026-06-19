# OS Language Design Specification

## Overview
A unified, highly efficient, fast, and secure systems programming language designed specifically for building operating systems. It aims to eliminate the need for mixing Assembly and C by providing low-level hardware control through a clean, high-level, "easy as hell" syntax.

## Architecture
The language compiler will utilize the **LLVM Framework**.
1. **Front-End (Lexer & Parser):** Reads the custom syntax and constructs an Abstract Syntax Tree (AST).
2. **Semantic Analyzer:** Enforces type safety, checks memory rules, and validates logical consistency.
3. **IR Generator:** Translates the validated AST into LLVM Intermediate Representation (IR).
4. **Backend (LLVM):** Takes the IR and compiles it into highly optimized, architecture-specific machine code (binary).

## Syntax & Semantics
The syntax is designed to be as readable and clutter-free as possible, heavily inspired by Python.

- **Block Structure:** Indentation-based (no curly braces `{}`).
- **Line Termination:** Newline-based (no semicolons `;`).
- **Typing:** Strongly typed with robust type inference. Explicit types are only required when the compiler cannot infer them (e.g., `let memory_buffer: [u8] = memory.allocate(1024)`).
- **Hardware Access:** Built-in semantic APIs for raw memory and hardware registers (e.g., `hardware.get_display()`), avoiding arcane pointer arithmetic.

## Memory Management
- **Safe by Default:** The compiler manages memory lifecycles automatically for general operations.
- **Explicit Unsafe Control:** For direct hardware manipulation (crucial for an OS), the language provides explicitly scoped low-level operations (e.g., raw byte allocation) that are clearly segregated from safe application logic.

## Initial Scope (Phase 1)
Build a Minimum Viable Compiler (MVC) capable of:
1. Lexing and parsing a basic `start_os()` function.
2. Generating a simple AST.
3. Emitting valid LLVM IR for that function.
