# OS Programming Language - Official Specification

## 1. Core Philosophy
The language is designed to allow developers to build operating systems from scratch using a syntax as clean and readable as Python, but compiling down to bare-metal performance using LLVM. It eliminates the need to mix C and Assembly by providing hardware access through specialized, structured syntax.

---

## 2. Basic Syntax & Types
The syntax uses Python-style indentation (spaces) instead of curly braces `{}` and avoids semicolons `;`.

### Primitive Types
- `int` (64-bit integer by default, with `u8`, `u16`, `u32`, `u64` for exact sizing)
- `float` (64-bit float by default, with `f32`, `f64`)
- `bool` (`true`, `false`)
- `str` (UTF-8 string literals)
- `char` (Single character)

### Variables & Mutability
Variables are immutable by default. To make them mutable, use `mut`. Types are inferred but can be explicitly declared.
```python
let name = "OS"                 # Immutable, inferred as string
let mut counter = 0             # Mutable, inferred as int
let buffer: [u8] = [0, 0, 0]    # Array of 8-bit unsigned integers
```

---

## 3. Control Flow
Standard branching and looping mechanics.
```python
if counter > 10:
    print("Done")
elif counter == 5:
    print("Halfway")
else:
    print("Keep going")

while counter < 10:
    counter = counter + 1
```

---

## 4. Functions
Functions are declared with the `fn` keyword. Return types are required if returning a value, otherwise inferred as `void`.
```python
fn add(a: int, b: int) -> int:
    return a + b
```

---

## 5. Data Structures: `struct` vs `hwmap`
Our language splits data structures into two distinct concepts to separate application logic from raw hardware interaction.

### Standard Structs (Application Logic)
Optimized by the compiler for speed. Padding and alignment are handled automatically.
```python
struct UserContext:
    id: int
    name: str
```

### Hardware Maps (Device Drivers)
`hwmap` strictly maps exactly to the hardware bytes. It guarantees perfectly packed, byte-aligned, and volatile memory access—essential for talking to Network Cards, USB controllers, and PCI devices.
```python
hwmap NetworkHeader:
    mac_destination: [u8; 6]
    mac_source:      [u8; 6]
    eth_type:        u16
```

---

## 6. Memory Management (Safe vs Unsafe)
By default, the compiler enforces strict memory borrowing rules (similar to Rust) so you never get segfaults or memory leaks.

To build drivers and touch hardware, you must use an `@unsafe` block or tag. In these blocks, you can manipulate raw pointers.

```python
@unsafe
fn write_to_vga(char: u8, position: int):
    let vga_buffer_ptr: ptr[u8] = 0xB8000
    vga_buffer_ptr[position] = char
```

---

## 7. Concurrency & Multi-core Safety
The language eliminates Deadlocks and Race Conditions at compile time through built-in syntax, avoiding the clunkiness of external Mutex libraries.

Data accessed across CPU cores must be declared `shared`. To modify it, you must enter a `lock` block. The compiler auto-generates the highly-optimized Spinlocks (for the kernel) or Mutexes (for user space) and guarantees they unlock when the block ends.

```python
shared let mut system_ticks = 0

fn timer_interrupt():
    lock system_ticks:
        system_ticks += 1
    # Automatically unlocked here. Cannot cause deadlocks!
```

---

## 8. OS & Hardware Operations
The language provides built-in syntax for low-level concepts:
- **Port I/O:** Reading/writing directly to CPU pins.
- **Interrupts:** Binding functions to hardware interrupts.

```python
# Hardware Port Communication
let key_code = hw.inb(0x60)     # Read byte from port 0x60 (Keyboard)

# Interrupt Handlers
@interrupt(33)                  # Bind to IRQ 1 (Keyboard)
fn handle_keyboard_press():
    let key = hw.inb(0x60)
```

---

## 9. Advanced CPU Control (Replacing Assembly)
Our language eliminates the need for `.asm` files entirely:

### Built-in CPU Intrinsics
```python
cpu.halt()          # Translates to `hlt`
cpu.disable_int()   # Translates to `cli`
```

### Inline Assembly
For ultra-specific context switches or Paging (`CR3` registers):
```python
@unsafe
fn load_page_directory(ptr: ptr[u32]):
    asm("mov cr3, {0}", in: ptr)
```

---

## 10. The Standard Library Ecosystem
Once the bare-metal core is built, the language will ship with a powerful Standard Library that allows OS developers to build high-level concepts natively:
- **`std.graphics` (Frontend):** Tools to draw windows, text, and 2D UI elements natively to the screen buffer.
- **`std.fs` (Database/Storage):** A built-in filesystem module to create files, folders, and read/write to hard drives (acting as the OS Registry and Database).
- **`std.net` (Backend):** TCP/UDP networking stacks to allow the OS to browse the web or act as a server.

---

## 11. Compiler Pipeline & Tooling
How code gets from text to a bootable OS:
1. **Lexical Analysis & Parsing:** Builds the AST.
2. **Semantic Analysis:** Enforces type checking and memory safety.
3. **IR Generation:** Translates AST into LLVM Intermediate Representation.
4. **Machine Code Emission:** LLVM optimizes and spits out raw `.o` files.
5. **Linking:** Links `.o` files with a bootloader script into a bootable `.bin` or `.iso`.

### Editor Support & Execution
The compiler toolchain will feature a native **Language Server Protocol (LSP)**, allowing VS Code and other editors to have syntax highlighting, auto-complete, and error checking for the language.

Running `compiler run os_kernel.os` will automatically compile the code and spin up a local **QEMU Virtual Machine**, letting the developer instantly see their OS boot up right inside their terminal/editor window.
