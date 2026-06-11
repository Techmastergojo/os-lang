# Requirements: OS Programming Language

**Defined:** 2026-06-11
**Core Value:** Provide absolute hardware control and memory safety without the cognitive load of traditional systems languages, making OS development "easy as hell."

## v1 Requirements

Requirements for the Minimum Viable Compiler (MVC).

### Lexing

- [ ] **LEX-01**: Tokenize keywords (`fn`, `let`, `if`, `print`)
- [ ] **LEX-02**: Tokenize identifiers and primitive literals (strings, numbers)
- [ ] **LEX-03**: Properly handle indentation and newline tokenization (Python-style blocks)

### Parsing

- [ ] **PAR-01**: Parse function declarations (`fn name():`)
- [ ] **PAR-02**: Parse variable assignments with optional type annotations (`let x: [u8] = y`)
- [ ] **PAR-03**: Parse function calls and member access (`hardware.get_display()`)
- [ ] **PAR-04**: Construct valid Abstract Syntax Tree (AST) nodes

### Semantic Analysis

- [ ] **SEM-01**: Perform basic type checking and type inference
- [ ] **SEM-02**: Detect and reject undefined variables and type mismatches

### LLVM Code Generation

- [ ] **IR-01**: Generate basic LLVM IR modules and function signatures
- [ ] **IR-02**: Translate AST instructions (variable assignment, calls) into LLVM IR instructions
- [ ] **IR-03**: Output LLVM object files or bitcode

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Standard Library

- **STD-01**: Create built-in wrappers for common hardware functions
- **STD-02**: Implement basic memory allocation wrappers safely

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Self-hosting compiler | The initial compiler will be built in an existing language to validate the architecture first. |
| Advanced Package Management | Not needed for the Minimum Viable Compiler. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LEX-01 | Phase 1 | Pending |
| LEX-02 | Phase 1 | Pending |
| LEX-03 | Phase 1 | Pending |
| PAR-01 | Phase 2 | Pending |
| PAR-02 | Phase 2 | Pending |
| PAR-03 | Phase 2 | Pending |
| PAR-04 | Phase 2 | Pending |
| SEM-01 | Phase 3 | Pending |
| SEM-02 | Phase 3 | Pending |
| IR-01 | Phase 4 | Pending |
| IR-02 | Phase 4 | Pending |
| IR-03 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-11*
*Last updated: 2026-06-11 after initial definition*
