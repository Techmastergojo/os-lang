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
# Cross-compiling a freestanding x86_64 kernel stub
osc kernel.os --target=x86_64-unknown-none --freestanding
```
*Note: The LLVM output (`output.o`) requires custom linking using `ld` to map the kernel into memory appropriately for bootloaders like GRUB.*

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
- `u8`, `u16`, `u64`: Unsigned integers of 8, 16, and 64 bits respectively. Essential for explicit hardware manipulation (e.g., `u16` for VGA text mode attributes).
- `usize`: Architecture-sized unsigned integer (32 or 64-bit), required for safe pointer offset arithmetic.
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

> ### ⚠️ WARNING: Pointer Scaling Rules
> 
> Pointer arithmetic in OS-Lang scales automatically based on the size of the underlying type if a pointer is cast to a specific type view. When performing raw byte-offset arithmetic, always ensure the base pointer is evaluated or cast as a `u8` or a flat `ptr`.

```python
def trigger_hardware():
    # Explicitly cast hex literal to raw architecture-width pointer
    var io_port: ptr = 0xCF8 as ptr
    
    @unsafe:
        # Dereferencing is explicitly fenced within the @unsafe boundary
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
    video_memory: u16[2000]

def print_a():
    # 0x0F41 is the hexadecimal for a white 'A' on black background in VGA text mode
    VGABuffer.video_memory[0] = 0x0F41
```
**Constraints:**
- The bound address must be known at compile time.
- All mapped fields must have fixed, static hardware dimensions.

---

## 8. Composite Types & Struct Alignment

Writing hardware drivers and network stacks requires defining strict, multi-variable payloads. OS-Lang achieves this through the `struct` construct.

### 8.1 Structure Syntax (`struct`)
Structures allow you to group multi-type variables into a single, continuous memory block using Pythonic syntax.
Fields are ordered sequentially in memory *exactly* as they are declared in code. 

```python
struct IDTEntry:
    offset_low: u16
    selector: u16
    ist: u8
    types_attr: u8
    offset_mid: u16
    offset_high: u32
    reserved: u32
```

### 8.2 The `@packed` Attribute Modifier
By default, the compiler naturally aligns types to hardware boundaries (e.g., aligning a `u32` on a 4-byte boundary) to optimize CPU fetch times. This creates invisible "padding bytes" between fields.

When mapping structures directly to hardware-defined registers or strict networking packet formats, padding corrupts the data structure. The `@packed` decorator forces the compiler to strip all padding bytes, collapsing the struct into an exact, dense memory footprint.

```python
# Applying hardware layouts cleanly
@packed
struct PageTableEntry:
    flags: u16
    physical_frame_number: u64
```

### 8.3 Nesting Structures in `hwmap`
The absolute power of OS-Lang’s readability shines when combining `struct` with `hwmap`. You can use a custom composite structure directly inside a memory map array.

```python
hwmap InterruptDescriptorTable at 0x1000:
    entries: IDTEntry[256]

def load_idt():
    # Setting up the first interrupt gate directly over hardware memory
    InterruptDescriptorTable.entries[0].offset_low = 0x0000
    InterruptDescriptorTable.entries[0].selector = 0x08
```

---

## 9. Inline Assembly & The Foreign Function Interface (FFI)

The technical bridge allowing OS-Lang to talk directly to CPU registers and ancestral C or Assembly initialization code.

### 9.1 The `asm` Execution Block Engine
Raw machine instructions can be evaluated directly inside an `@unsafe` segment. This is critical for operations that cannot be expressed in high-level syntax (e.g., loading the IDT).

```python
def load_idt_register(idt_ptr: ptr):
    @unsafe:
        asm("lidt (%0)" : : "r"(idt_ptr) : "memory")
```

### 9.2 The `@naked` Function Attribute
The `@naked` attribute strips automatic compiler prologues and epilogues (no stack pushes, no base pointer tracking). This allows you to write raw interrupt handlers that cleanly manage their own entry and exit states via assembly (`iretq`).

```python
@naked
def page_fault_handler():
    @unsafe:
        asm("pusha")
        # Handle fault
        asm("popa")
        asm("iretq")
```

### 9.3 Cross-Language Linking (`extern "C"`)
To link against ancestral binaries or bootloader objects written in C, declare foreign functions using `extern "C"`.

```python
extern "C" def kmain(multiboot_magic: u32, multiboot_info: ptr) -> !:
    # OS entry point called by GRUB
    pass
```

### 9.4 Symbol Preservation Attributes (`@no_mangle` / `@export`)
To prevent LLVM from renaming symbols during the optimization pass (essential for `_start` or `kmain` functions called by assembly bootloaders), use the `@no_mangle` attribute.

---

## 10. Core Freestanding Runtime Engine (`no_std` Architecture)

When running without a host OS layer, the compiler provides the absolute minimum safety scaffolds.

### 10.1 The Master Panic Signature
Upon an unrecoverable failure (e.g., an unhandled exception or an explicit `panic()`), the compiler redirects execution to a uniform panic handler. The kernel developer *must* define this intercept routine.

```python
@no_mangle
def on_panic(file: ptr, line: u32, reason: ptr) -> !:
    # Disable interrupts and halt CPU
    @unsafe:
        asm("cli; hlt")
```

### 10.2 Core Allocation Engine Traits
OS-Lang assumes no heap. Developers must implement the uniform interface models to route expressions like `new` directly to a custom physical page allocator or buddy allocator system. Until this is manually hooked up, all dynamic allocations trigger compilation errors.

---

## 11. Testing, Cross-Validation & Debugging Systems

### 11.1 Debug Symbol Generation
To inject explicit DWARF data tracking frames alongside machine code, pass the `-g` flag to the compiler.
```bash
osc kernel.os --target=x86_64-unknown-none --freestanding -g
```

### 11.2 Active Debug Server Hookup
To trace kernel execution, launch QEMU with a GDB stub:
```bash
qemu-system-x86_64 -kernel kernel.bin -s -S
```
Then, connect a live GDB execution instance:
```bash
gdb kernel.o -ex "target remote localhost:1234"
```

---

## 12. Compiler Diagnostics & Undefined Behavior Matrix

The OS-Lang parser provides an exhaustive diagnostic registry.

### 12.1 Alphanumeric Error Registry
- **E001 (Access Faults):** Attempting low-level pointer interaction without an open `@unsafe` boundary block.
- **E002 (Type Misalignments):** Forcing variable conversions without passing an explicit `as` casting modifier.
- **E003 (Indentation Mismatch):** Bad whitespace blocks halting the lexical compilation sequence.

### 12.2 Undefined Behavior Warning Appendix
The compiler parser cannot validate the following hardware scenarios at compile time. These will cause severe runtime failures (Undefined Behavior):
- Misaligned hardware lookups (e.g., reading a `u32` from a non-4-byte aligned boundary).
- Tracking across uninitialized memory fields.
- Illegal out-of-bounds pointer loops inside an `@unsafe` block.
- Casting an arbitrary integer to a function pointer that does not point to valid machine instructions.
