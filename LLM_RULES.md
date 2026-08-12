# OS-Lang LLM Rules & Language Specification

This document provides strict grammatical, semantic, and intrinsic rules for AI assistants (GPT, Claude, Gemini, Copilot, Cursor) writing or modifying `.os` and `.osext` files.

---

## 1. Syntax Essentials

### Function Definition
Functions MUST use `fn`, typed parameters, and return type with colon.
```python
# CORRECT
fn add(a: int, b: int) -> int:
    return a + b

fn no_return(x: u32) -> void:
    pass

# INCORRECT (DO NOT WRITE THIS)
# def add(a, b):          <-- WRONG: Do not use 'def'
# fn add(a, b) { ... }    <-- WRONG: Do not use curly braces '{}'
# fn add(a: int);         <-- WRONG: Do not use semicolons ';'
```

### Variable Declarations
Variables MUST be explicitly typed and declared with `let` or `let mut`.
```python
# CORRECT
let count: int = 0
let mut status: u32 = 100
let name: str = "Leopard"

# INCORRECT (DO NOT WRITE THIS)
# count = 0               <-- WRONG: Missing 'let' or 'let mut'
# var count: int = 0      <-- WRONG: Do not use 'var'
```

### Primitive Types
- Integers: `u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`, `int`
- Pointers: `ptr` or `ptr[u32]` or `ptr[u8]`
- Strings & Chars: `str`, `char`
- Arrays: `[u8; 16]` or `[int]`

---

## 2. Safety & Low-Level Decorators

Hardware manipulation, pointer dereferencing, port I/O, atomics, and inline assembly MUST be decorated with `@unsafe`.

### Hardware Map (`hwmap`)
Use `hwmap` instead of `struct` for memory-mapped hardware structures:
```python
@unsafe
hwmap VgaChar:
    ascii_char: u8
    color_code: u8
```

### Decorator Catalog
- `@unsafe`: Guard for raw pointer dereferencing, port I/O, inline assembly.
- `@interrupt(vector_num)`: ISR vector handler (e.g. `@interrupt(33)` for keyboard IRQ1).
- `@entry`: Kernel entry point function (e.g. `kmain`).
- `@naked`: Omit standard stack frame prologue/epilogue (context switching).
- `@syscall(num)`: System call entry point (e.g. `@syscall(1)`).
- `@driver`: Hardware driver initialization function.
- `@noreturn`: Function never returns (e.g. `panic()`).

---

## 3. LEX Extensions (`.osext`)

Extensions MUST use LEX decorators:
```python
@meta(author="Hamza", version="1.0.0", description="Custom Driver")
@extend

@override(target="original_fn_name")
@unsafe
fn custom_fn_name():
    pass
```

---

## 4. Built-in Low-Level Hardware Helpers & Intrinsics

You can call these built-in hardware helpers without external imports inside `@unsafe` functions:

| Intrinsic / Helper | Description |
|---|---|
| `inb(port: int) -> int` | Read byte from I/O port |
| `outb(port: int, val: int) -> void` | Write byte to I/O port |
| `inw(port: int) -> int` | Read 16-bit word from I/O port |
| `outw(port: int, val: int) -> void` | Write 16-bit word to I/O port |
| `cli() -> void` | Disable CPU interrupts |
| `sti() -> void` | Enable CPU interrupts |
| `halt() -> void` | Halt CPU until next interrupt |
| `rdtsc() -> int` | Read CPU timestamp counter |
| `vga_write(x: int, y: int, char: u8, color: u8)` | Write character & color to VGA buffer (0xB8000) |
| `draw_cursor(x: int, y: int, color: u8)` | Draw mouse cursor on VGA screen |
| `draw_pixel(x: int, y: int, color: u32)` | Write pixel to framebuffer |
| `volatile_load(ptr, offset)` | Volatile read from memory pointer |
| `volatile_store(ptr, offset, val)` | Volatile write to memory pointer |

---

## 5. Concise Driver Examples for AI

### 4-Line Keyboard Driver
```python
@interrupt(33)
fn keyboard_handler():
    let key: int = inb(0x60)
    vga_write(0, 0, key as u8, 15)
    outb(0x20, 0x20)
```

### 5-Line Mouse Cursor Renderer
```python
@unsafe
fn render_mouse(x: int, y: int):
    draw_cursor(x, y, 14)
```

### 3-Line VGA Printer
```python
@unsafe
fn print_char(ch: u8):
    vga_write(0, 0, ch, 15)
```
