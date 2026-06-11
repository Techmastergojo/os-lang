# Roadmap: OS Programming Language

**Goal:** Build the Minimum Viable Compiler (MVC) for the new OS programming language.

## Phase 1: Lexical Analysis (Lexer)
- **Status**: Not Started
- **Goal**: Read source code and output a stream of tokens, correctly handling Python-like indentation.
- **Requirements**: LEX-01, LEX-02, LEX-03
- **Steps**:
  1. Setup project structure and CLI entry point.
  2. Implement keyword tokenization (`fn`, `let`, `if`, etc.).
  3. Implement string and numeric literal tokenization.
  4. Implement indentation and dedentation logic for blocks.
  5. Add tests for the lexer.

## Phase 2: Syntax Analysis (Parser)
- **Status**: Not Started
- **Goal**: Take the token stream and build an Abstract Syntax Tree (AST).
- **Requirements**: PAR-01, PAR-02, PAR-03, PAR-04
- **Steps**:
  1. Define AST node data structures (Expressions, Statements, Functions).
  2. Implement parsing for variable declarations (`let`).
  3. Implement parsing for function calls.
  4. Implement parsing for function definitions.
  5. Add tests for the parser.

## Phase 3: Semantic Analysis
- **Status**: Not Started
- **Goal**: Traverse the AST to perform type checking and validation.
- **Requirements**: SEM-01, SEM-02
- **Steps**:
  1. Implement a Symbol Table to track variables and types.
  2. Add type inference for simple assignments.
  3. Detect and throw errors for undefined variables.
  4. Detect and throw errors for type mismatches.
  5. Add tests for the semantic analyzer.

## Phase 4: Code Generation (LLVM IR)
- **Status**: Not Started
- **Goal**: Translate the validated AST into LLVM Intermediate Representation.
- **Requirements**: IR-01, IR-02, IR-03
- **Steps**:
  1. Setup LLVM bindings (e.g., using `llvmlite` if in Python, or native LLVM API in C++/Rust).
  2. Generate IR for basic math and variable storage.
  3. Generate IR for function definitions.
  4. Emit the IR to a `.ll` file.
  5. Compile the `.ll` file to an object file using the LLVM backend.
