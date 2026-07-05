---
slug: /
title: OS-Lang Documentation
hide_table_of_contents: false
---

<div className="heroBanner">
  <div className="heroText">
    <h1 className="heroTitle">OS-Lang</h1>
    <p className="heroSubtitle">An intuitive, memory-safe, and highly optimized systems language.</p>
    <div className="buttons">
      <a className="button button--primary" href="#installation--setup">Download OS-Lang 1.0.0</a>
      <a className="button button--secondary" href="#what-is-os-lang">Read the Docs</a>
    </div>
  </div>
</div>

<br />

# What is OS-Lang?

**OS-Lang** is a next-generation systems programming language compiled directly to LLVM IR. It was designed from the ground up for one specific purpose: **writing bare-metal operating systems, kernels, and hardware drivers.**

## Why OS-Lang?

Writing an OS today is painful. You have to write brittle inline assembly in C, link against complex linker scripts, and manually manage memory alignment with ugly GNU extensions (`__attribute__((packed))`). 

OS-Lang solves this by bringing the clean, expressive syntax of modern languages to Ring 0, while compiling down to zero-overhead CPU instructions.

## Why use OS-Lang?

- **Built-in Intrinsics:** Call CPU instructions like `cli()`, `sti()`, `inb()`, and `outb()` as regular functions.
- **Hardware Native:** Features like `@packed` structs ensure memory maps perfectly to hardware descriptor tables without LLVM padding.
- **Interrupt Safety:** The `@interrupt` decorator automatically sets the `x86_intrcc` calling convention for safe context switching.
- **Modern Ergonomics:** Enums, Pattern Matching, and Type Inference make kernel logic beautiful and readable.

---

# Comparison to C and Rust

How does OS-Lang compare to the two most popular systems languages?

## OS-Lang vs C

C has been the king of OS development for decades, but it lacks strict safety boundaries.

- **Memory Safety:** In C, any pointer can overwrite any memory address at any time. In OS-Lang, all pointer dereferences **must** be wrapped in an `@unsafe:` block, isolating hardware manipulation from your core kernel logic.
- **Modern Syntax:** OS-Lang replaces archaic `switch` blocks with expressive Pattern Matching (`match`) and zero-cost `enum` types.
- **No Inline Assembly:** OS-Lang provides compiler intrinsics for typical CPU operations, eliminating the need for hard-to-read `__asm__` blocks.

## OS-Lang vs Rust

Rust is incredibly memory safe, but its famous "borrow checker" can be a massive hurdle when writing a kernel, where memory is inherently shared and global.

- **Simpler Learning Curve:** OS-Lang focuses on pragmatic safety through `@unsafe` isolation without forcing the developer to fight complex lifetime annotations or Arc/Mutex wrappers just to write to a VGA buffer.
- **Purpose-Built for Bare Metal:** Rust is a general-purpose language. OS-Lang was explicitly built for operating systems, providing native `@interrupt` decorators and hardware alignment tools out-of-the-box.

---

# Installation & Setup

Getting started with OS-Lang is incredibly fast. The compiler is written in Python and uses `llvmlite` to generate LLVM IR.

## 1. Install via pip

To install the compiler globally on your system:

```bash
pip install os-lang
```

This will give you access to the `osc` (OS-Lang Compiler) CLI tool.

## 2. VS Code Extension

To get beautiful syntax highlighting, download our official Visual Studio Code extension.

1. Download the `.vsix` package from the [OS-Lang GitHub Releases](https://github.com/Techmastergojo/os-lang).
2. Open VS Code, go to the Extensions view.
3. Click the `...` menu and select **"Install from VSIX..."**
4. Choose the downloaded file.

---

# Environment Setup (QEMU)

To run the operating system you write in OS-Lang, you will need a virtual machine emulator like **QEMU**.

## Installing QEMU

**Windows:**
Download the binaries from the official [QEMU website](https://www.qemu.org/download/).

**macOS:**
```bash
brew install qemu
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install qemu-system-x86
```

## Compiling Your First Kernel

OS-Lang compiles to an object file (`.o`), which you then link using standard GNU tools or `lld`.

```bash
# 1. Compile OS-Lang to LLVM IR and then to an object file
python build_kernel.py

# 2. Run in QEMU
qemu-system-x86_64 -kernel kernel.bin
```

---

# Memory Safety & `@unsafe`

Because OS-Lang allows direct hardware manipulation, it enforces strict boundaries to prevent memory corruption in high-level business logic. All direct memory access via pointers **must** reside within an `@unsafe:` block.

### Example: Writing to the VGA Buffer

```os-lang
fn main() -> int:
    let mut address: int = 0xB8000
    let mut vga_buffer: *mut u16 = address as *mut u16
    
    # Safely guarded raw memory access
    @unsafe:
        let val: u16 = *vga_buffer
        *vga_buffer = 0x0F41  # Write 'A' (white on black) to the screen
        
    return 0
```

---

# Hardware Alignment (`@packed`)

When mapping structs directly to hardware memory (e.g., GDT entries or IDT descriptors), LLVM padding can corrupt the layout.

Use the `@packed` decorator to enforce zero-padding.

```os-lang
@packed
struct IdtEntry {
    offset_low: u16
    selector: u16
    ist: u8
    type_attr: u8
    offset_mid: u16
    offset_high: u32
    zero: u32
}

fn initialize_idt() -> void:
    # sizeof() calculates byte-width at compile time
    let entry_size: int = sizeof(IdtEntry)
    print(entry_size) # Outputs exactly 16 bytes!
```

---

# Pattern Matching (`match`)

Instead of managing floating integer constants, OS-Lang provides zero-cost `enum` types and the `match` statement. `match` is compiled down directly to highly optimized LLVM `switch` tables, ensuring `O(1)` branching performance.

```os-lang
enum ThreadState {
    RUNNING,
    BLOCKED,
    SLEEPING
}

fn process_thread(state: ThreadState) -> void:
    match state:
        ThreadState.RUNNING =>:
            print("Executing...")
        ThreadState.BLOCKED =>:
            print("Waiting for I/O")
        _ =>:
            print("Default catch-all for sleeping")
```

---

# Creating an ASCII Keyboard Driver

This example demonstrates how to read scan codes from the PS/2 keyboard port, handle the hardware interrupt, and map scancodes to ASCII characters using pattern matching.

### 1. The Port I/O Setup

We use OS-Lang's built-in `inb()` and `outb()` hardware intrinsics to talk to the keyboard controller (Port `0x60`) and the Programmable Interrupt Controller (PIC at `0x20`).

### 2. The Implementation

```os-lang
# Global Scancode to ASCII Mapper
fn map_scancode_to_ascii(scancode: u8) -> u8:
    match scancode:
        0x1E =>: # 'A'
            return 65
        0x30 =>: # 'B'
            return 66
        0x2E =>: # 'C'
            return 67
        _ =>:
            return 0 # Unknown key

# The Hardware Interrupt Handler (IRQ 1 for Keyboard)
@interrupt(33)
fn keyboard_interrupt_handler() -> void:
    # 1. Read the scancode from PS/2 Port 0x60
    let scancode: u8 = inb(0x60)
    
    # 2. Only process key-down events (top bit is 0)
    if scancode < 0x80:
        let ascii_char: u8 = map_scancode_to_ascii(scancode)
        if ascii_char != 0:
            print_char(ascii_char)
            
    # 3. Send End of Interrupt (EOI) to the PIC so it sends more interrupts
    outb(0x20, 0x20)
```

### Explanation

1. **`@interrupt(33)`**: This decorator tells the OS-Lang compiler to apply the `x86_intrcc` calling convention, ensuring all CPU registers are safely pushed before execution and popped before sending the `iretq` instruction.
2. **`inb(0x60)`**: This compiler intrinsic reads a single byte from the hardware port.
3. **`outb(0x20, 0x20)`**: Acknowledges the interrupt to the PIC. If you forget this, your keyboard will only work once!
