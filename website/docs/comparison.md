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
