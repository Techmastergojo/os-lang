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
