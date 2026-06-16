# OS-Lang: A Next-Generation Language for Bare-Metal Development

[![PyPI version](https://badge.fury.io/py/os-lang.svg)](https://badge.fury.io/py/os-lang)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OS-Lang (`.os`)** is a brand new, highly-opinionated programming language specifically designed for writing bare-metal operating systems, kernels, and low-level system software. It combines the clean, fast, indentation-based syntax of Python with the raw, bare-metal memory control of C and Rust.

If you are tired of setting up complex C++ makefiles or fighting the Rust borrow checker just to write a simple VGA text-mode driver or memory allocator, OS-Lang is for you.

## Why OS-Lang?
When building an operating system, a language must compile directly to bare-metal machine code, manage raw memory addresses manually, and interface with hardware without relying on an underlying OS or garbage collector. OS-Lang achieves this seamlessly by compiling directly to **LLVM IR**.

- **Pythonic Syntax**: No semicolons, no curly braces, strict indentation.
- **Bare-Metal Compilation**: Compiles directly to object files (`.o`) via LLVM.
- **No Runtime/Garbage Collector**: You have 100% control over memory.
- **Hardware Maps (`hwmap`)**: A powerful paradigm for mapping C-style structs directly to volatile hardware memory registers.
- **Intrinsic OS Support**: First-class support for `volatile_load`, `volatile_store`, and CPU intrinsics.
- **Explicit Safety (`@unsafe`)**: Hardware manipulation is strictly guarded by explicit unsafe scopes.

## Installation

OS-Lang is available on the global Python Package Index (PyPI). You can install it instantly:

```bash
pip install os-lang
```

## Quick Start

Create a new file called `kernel.os`:

```python
# kernel.os
@unsafe
hwmap VgaChar:
    ascii_char: u8
    color_code: u8

@unsafe
fn _start() -> void:
    let vga_buffer: *VgaChar = 0xB8000
    let text: u8 = 79  # 'O'
    let color: u8 = 15 # White text, black background
    
    # Direct volatile memory manipulation to print to the screen
    volatile_store(vga_buffer, 0, VgaChar(text, color))

    while true:
        pass
```

Compile it using the CLI:
```bash
osc kernel.os
```

Or, use the **Desktop GUI App**:
```bash
osc-gui
```

This will instantly generate `kernel.ll` (LLVM IR) and `kernel.o` (Machine Code), ready to be linked with a bootloader like GRUB!

## Documentation

See the `docs/` directory for full documentation:
- **[Language Reference](docs/LANGUAGE_REFERENCE.md)**: Syntax, Types, and Primitives.
- **[OS Core Definitions](os_core.os)**: Standard structures for Task State and Interrupt Frames.

## The Playground
You can run the web-based interactive compiler playground locally:
```bash
pip install -r requirements.txt
python playground/app.py
```
Then visit `http://localhost:5000` to write and compile OS code right in your browser!

## License
MIT License. See `LICENSE` for details.
