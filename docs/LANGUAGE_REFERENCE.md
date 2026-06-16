# Next-Generation OS Development Language Reference

## 1. Introduction
This document serves as the full language reference for the Next-Generation OS Development Language. The language is designed to have Pythonic readability with C-level control and performance. 

## 2. Program Structure

### 2.1 File Extension
All source code files must end in `.os`.

### 2.2 Indentation
Blocks of code are defined by indentation (4 spaces recommended). There are no curly braces `{}` or semicolons `;`.

```os
fn main() -> int:
    let x: int = 0
    return x
```

## 3. Data Types

### 3.1 Primitive Types
- **Integers:** `u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`, `int`
- **Floating Point:** `f32`, `f64`, `float`
- **Boolean:** `bool` (values: `true`, `false`)
- **Strings/Characters:** `str`, `char`

### 3.2 Complex Types
- **Pointers:** `ptr[T]` where T is the underlying type.
- **Arrays:** `[T; size]` statically sized.

### 3.3 Data Structures
- **struct:** General-purpose application structures.
  ```os
  struct Point:
      x: int
      y: int
  ```
- **hwmap:** Hardware maps, strictly packed with zero padding, essential for memory-mapped I/O.
  ```os
  hwmap RegisterBank:
      control: u32
      status: u32
  ```

## 4. Variables & Immutability

By default, all variables are immutable. Use the `mut` keyword to allow mutation.

```os
let x: int = 10        # Immutable
let mut y: int = 20    # Mutable
y = 30
```

## 5. Control Flow

### 5.1 If / Elif / Else
```os
if condition:
    pass
elif other_condition:
    pass
else:
    pass
```

### 5.2 Loops
*(Support for `for` and `while` loops follows standard Python conventions)*

## 6. Functions & Decorators

Functions are declared with `fn` and optionally return a type:
```os
fn compute_sum(a: int, b: int) -> int:
    return a + b
```

### 6.1 Decorators
Decorators provide compiler metadata or enable special behavior:
- `@unsafe`: Permits raw memory manipulation, inline assembly, and atomic operations.
- `@naked`: Disables standard prologue/epilogue for custom inline assembly.
- `@interrupt(num)`: Binds a function to an interrupt descriptor.
- `@entry`: Marks the entry point of the binary.

## 7. OS Development Features (Unsafe Environment)

The following operations require the function to be decorated with `@unsafe`.

### 7.1 Inline Assembly
Execute arbitrary machine code instructions directly.
```os
asm("cli")
```

### 7.2 Hardware I/O
Interact directly with the CPU's I/O ports.
```os
let data: u8 = inb(0x60)
outb(0x60, 0xFF)
```

### 7.3 Volatile Memory Operations
Bypass compiler optimizations for memory-mapped hardware interactions.
- `volatile_load(ptr: ptr[T]) -> T`
- `volatile_store(ptr: ptr[T], val: T)`

### 7.4 Atomics
Thread-safe primitives for building spinlocks and synchronization structures. Uses sequential consistency (`seq_cst`).
- `atomic_xchg(ptr: ptr[T], val: T) -> T`
- `atomic_cmpxchg(ptr: ptr[T], expected: T, val: T) -> T`
- `atomic_add(ptr: ptr[T], val: T) -> T`
- `atomic_sub(ptr: ptr[T], val: T) -> T`

## 8. C Interoperability (Coming Soon)
Foreign function interface to call standard C libraries:
```os
extern "C" fn printf(fmt: str, ...) -> int
```
