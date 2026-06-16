---
name: os-language-coder
description: "Teaches the AI how to write and understand the Next-Generation OS Development Language."
---

# SKILL: OS-Language Coder

## TRIGGER
When the user asks to write `.os` files, mentions the OS language, or asks to build kernel drivers, modules, or standard library code for the Next-Gen OS Language.

## SYNTAX RULES

### Basics
- **Functions:** `fn name(arg: type) -> type:`
- **Variables:** `let name: type = value` (immutable by default)
- **Mutable Variables:** `let mut name: type = value`
- **Comments:** Use `#` for single-line comments

### Types
- **Integers:** `u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`, `int`
- **Floats:** `f32`, `f64`, `float`
- **Other:** `bool`, `str`, `char`
- **Arrays:** `[type; size]` (e.g., `[u8; 4096]`)
- **Pointers:** `ptr[type]` (e.g., `ptr[u32]`) or just `ptr`

### Memory Safety & OS Primitives
- **Unsafe blocks/functions:** Prefix functions with `@unsafe` to allow raw pointer manipulation, inline assembly, and volatile operations.
- **Hardware Maps:** Use `hwmap Name:` instead of `struct` when defining packed, exact-byte-aligned structures for hardware registers.
- **Structs:** Use `struct Name:` for general application data structures.

### Control Flow
- Indentation-based blocks (like Python). No curly braces `{}`.
- **Conditionals:**
```os
if condition:
    # do something
elif other_condition:
    # do something else
else:
    # default
```

### OS Intrinsics (Requires `@unsafe`)
- **Inline ASM:** `asm("instruction")`
- **Volatile Memory:**
  - `volatile_load(ptr: ptr[type]) -> type`
  - `volatile_store(ptr: ptr[type], value: type)`
- **Atomics (Sequential Consistency):**
  - `atomic_xchg(ptr: ptr[type], val: type) -> type`
  - `atomic_cmpxchg(ptr: ptr[type], cmp: type, val: type) -> type`
  - `atomic_add(ptr: ptr[type], val: type) -> type`
  - `atomic_sub(ptr: ptr[type], val: type) -> type`

### Decorators
- `@unsafe`: Allows dangerous operations.
- `@naked`: Disables compiler prologue/epilogue for custom assembly (e.g., context switching).
- `@interrupt(num)`: Binds a function to an interrupt vector.
- `@entry`: Marks the entry point of the kernel or application.

## EXAMPLE: Kernel Context Switch
```os
hwmap TaskState:
    eax: u32
    ebx: u32
    eip: u32

@naked
@unsafe
fn context_switch():
    asm("pusha")
    asm("popa")
    asm("iret")
```

## GUIDELINES
1. **Never** use C-style curly braces for control flow or functions.
2. Ensure hardware interactions and raw pointer uses are inside `@unsafe` functions.
3. Use `hwmap` for hardware descriptors, not `struct`.
