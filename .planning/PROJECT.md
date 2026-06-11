# OS Programming Language

## What This Is

A unified, highly efficient, fast, and secure systems programming language designed specifically for building operating systems. It aims to eliminate the need for mixing Assembly and C by providing low-level hardware control through a clean, high-level, Python-like syntax. The compiler will use LLVM as its backend to generate optimized machine code.

## Core Value

Provide absolute hardware control and memory safety without the cognitive load of traditional systems languages, making OS development "easy as hell."

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Lexer: Tokenize the Python-like indentation-based syntax.
- [ ] Parser: Construct an Abstract Syntax Tree (AST) from tokens.
- [ ] Semantic Analyzer: Enforce type safety and memory rules.
- [ ] LLVM IR Generator: Translate the validated AST into LLVM Intermediate Representation (IR).
- [ ] Backend: Compile the IR into an object file or binary using LLVM.

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- [Advanced Standard Library] — Keep the initial compiler minimal (MVC) to validate the core architecture first.
- [Self-hosting] — The initial compiler will be built in an existing language (likely Python or Rust/C++) before rewriting the compiler in its own language.

## Context

- The project relies on the LLVM compiler infrastructure.
- The syntax avoids curly braces `{}` and semicolons `;` in favor of indentation and newlines.
- Explicit low-level operations (like `memory.allocate`) are provided for OS hardware manipulation.

## Constraints

- **Tech stack**: LLVM backend is required.
- **Performance**: Must produce machine code comparable to C/Rust in execution speed.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use LLVM | Industry-standard optimization and hardware support out of the box. | — Pending |
| Python-like Syntax | Maximizes readability and makes systems programming accessible. | — Pending |

---
*Last updated: 2026-06-11 after project initialization*
