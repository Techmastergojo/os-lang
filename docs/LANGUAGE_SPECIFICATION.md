# OS-Lang: Official Language Specification & Master Reference

This document serves as the definitive reference guide for OS-Lang. It bridges the gap between Python-like readability and the uncompromising, raw hardware requirements of operating system development.

---

## 1. Environment Setup & Compiler Toolchain

OS-Lang is designed as a standalone, hostless systems programming language. The compiler produces LLVM IR, which is subsequently assembled into raw machine binaries.

### 1.1 Toolchain Installation
The OS-Lang compiler suite can be installed globally via PyPI.
```bash
pip install os-lang
```
This exposes two primary commands:
- `osc`: The command-line compiler.
- `osc-gui`: A lightweight IDE and graphical compiler.

### 1.2 The Build Pipeline
The `osc` tool reads a `.os` source file and generates an LLVM Object File (`.o`).
To compile an OS-Lang file for a bare-metal environment:
```bash
osc kernel.os
```
*Note: The LLVM output (`output.o`) is currently compiled for your host architecture. To compile for freestanding bootloaders, custom linking using `ld` and architecture-specific flags are required.*

---

## 2. Lexical Structure & Grammar

OS-Lang relies heavily on a Pythonic, indentation-based grammar. 

### 2.1 Indentation & Blocks
Code blocks are defined purely by indentation (4 spaces). There are no curly braces `{}` or semicolons `;`.
```python
def example():
    var a: i32 = 10
    if a == 10:
        a = 20
```

### 2.2 Keywords
The language reserves the following core keywords: 
`def`, `var`, `if`, `else`, `while`, `return`, `hwmap`, `at`, `@unsafe`.

---

## 3. Fixed-Width Type System

As an OS language, memory footprint must be entirely predictable. There is no dynamic typing.

### 3.1 Primitive Types
- `i32`: 32-bit signed integer.
- `u8`: 8-bit unsigned integer (commonly used for raw byte/character manipulation).
- `ptr`: Raw memory pointer (architecture-dependent width, usually 32 or 64-bit).

### 3.2 Variable Declaration
Variables are strictly typed and defined using the `var` keyword.
```python
var counter: i32 = 0
var status_flag: u8 = 1
```

---

## 4. Control Flow

### 4.1 Conditional Statements
Standard `if` and `else` branching is supported. Evaluation conditions must resolve cleanly.
```python
if counter == 0:
    counter = 1
else:
    counter = 2
```

### 4.2 Looping Mechanisms
Currently, the primary polling loop architecture relies on `while`. This is essential for hardware status polling (e.g., waiting for an I/O port to clear).
```python
while counter < 10:
    counter = counter + 1
```

---

## 5. Functions & Signatures

Functions must strictly annotate their argument types and return values. Type coercion is strictly banned at function boundaries to ensure Application Binary Interface (ABI) stability.

```python
def add_numbers(a: i32, b: i32) -> i32:
    return a + b
```

---

## 6. Low-Level Memory Management & `@unsafe`

OS-Lang has no garbage collector and no implicit memory safety overhead. The developer has total authority over memory.

### 6.1 The `@unsafe` Containment Model
By default, the compiler prevents raw memory access. To read, write, or manipulate raw hardware addresses, developers must explicitly open an `@unsafe` context.

```python
def trigger_hardware():
    var io_port: ptr = 0xCF8
    @unsafe:
        *io_port = 0x1
```
*Note: The `*` token acts as the standard dereference operator for pointers.*

---

## 7. Hardware Maps (`hwmap`)

Writing bare-metal drivers requires constant interaction with structured memory (like VGA buffers, IDTs, or GDTs). Instead of relying on manual pointer arithmetic, OS-Lang provides `hwmap`.

### 7.1 Declaring a Hardware Map
A `hwmap` binds a structured payload exactly onto a physical memory address at compile time.

```python
hwmap VGABuffer at 0xB8000:
    video_memory: u8[4000]

def print_a():
    VGABuffer.video_memory[0] = 65
    VGABuffer.video_memory[1] = 15
```
**Constraints:**
- The bound address must be known at compile time.
- All mapped fields must have fixed, static hardware dimensions.

---

## 8. Compiler Diagnostics & Errors

The OS-Lang parser provides strict diagnostics for:
- **Type Misalignments:** Trying to assign an `i32` to a `u8` without explicit casting.
- **Unsafe Violations:** Attempting to dereference a `ptr` outside an `@unsafe` block.
- **Indentation Faults:** Misaligned block structures will immediately halt code generation.

*More comprehensive ABI integrations, FFI declarations, and structured data compositions (`struct`) will be formally detailed as the `no_std` kernel core environment expands.*
