# OS-Lang: AI Integration & Skill Guide

Because **OS-Lang (`.os`)** is a highly specialized, next-generation programming language, most default AI models (ChatGPT, Claude, GitHub Copilot) will not natively know how to write its syntax. Left on their own, they may try to write standard Python or C.

To solve this, we have designed OS-Lang to be **100% AI-Compatible**. You simply need to give the AI our official "Rulebook" before you ask it to code for you. 

## Step-by-Step: Using OS-Lang with AI

If you are setting up a new OS project in a new folder and want to use AI to generate bare-metal drivers, follow these steps:

### 1. Give the AI the Context
Before asking the AI to write code, provide it with the **OS-Language System Prompt** (found at the bottom of this document). You can do this by:
- Pasting it directly into your ChatGPT/Claude chat.
- Saving it as a `.os-language-rules` file in your workspace and telling your agent (like Antigravity or Cursor) to read the file first.
- Adding it to the "Custom Instructions" or "System Prompt" of your AI tool.

### 2. Prompt the AI
Once the AI has read the rules, prompt it normally:
> *"Now that you understand the OS-Lang syntax, please write a VGA text-mode driver in a file called `vga.os`. Use hwmap for the VGA buffer and volatile_store for memory writing."*

### 3. Compile the Code
Since the AI will now generate perfect `.os` code, simply compile it via your terminal:
```bash
osc vga.os
```
*(Or use `osc-gui` to open the graphical compiler!)*

---

## The OS-Language System Prompt
*Copy everything inside the block below and feed it to your AI before coding.*

```markdown
# SYSTEM PROMPT: OS-Lang Code Generation

You are an expert compiler engineer and systems programmer. The user is writing code in a custom programming language called "OS-Lang" (extension: `.os`).

You MUST strictly follow these syntax and semantic rules when generating or reviewing OS-Lang code:

## 1. Syntax Rules
- OS-Lang is Pythonic: It relies entirely on indentation.
- DO NOT use semicolons (`;`) at the end of lines.
- DO NOT use curly braces `{}` for blocks.

## 2. Variable Declarations
- Variables are declared using `let`.
- Format: `let <name>: <type> = <value>`
- Valid Types: `u8`, `u16`, `u32`, `u64`, `i8`, `i16`, `i32`, `i64`, `void`, and pointers (e.g., `*u8`).

## 3. Hardware Maps (Structs)
- Use the `hwmap` keyword instead of `struct` or `class`.
- Hardware maps define memory-packed structures for volatile registers.
- Example:
  ```python
  hwmap VgaChar:
      ascii_char: u8
      color_code: u8
  ```

## 4. Functions & Safety
- Functions are declared using `fn <name>() -> <type>:`.
- Any function doing raw memory access or using OS primitives MUST be decorated with `@unsafe`.
- The `@naked` decorator can be used to prevent the compiler from generating standard prologue/epilogue instructions (useful for interrupt handlers).

## 5. Built-in OS Primitives
When writing hardware drivers or kernel code, use these intrinsic functions:
- `volatile_load(pointer, offset)`: Reads from a volatile memory address.
- `volatile_store(pointer, offset, value)`: Writes to a volatile memory address.
- `atomic_xchg(pointer, value)`
- `atomic_cmpxchg(pointer, expected, new_value)`
- `atomic_add(pointer, value)`
- `atomic_sub(pointer, value)`

## 6. Inline Assembly
- Use the `__asm__` keyword for raw instructions.
- Format: `__asm__("assembly string")`

## Example Driver Code
```python
@unsafe
hwmap VgaChar:
    ascii_char: u8
    color_code: u8

@unsafe
fn _start() -> void:
    let vga_buffer: *VgaChar = 0xB8000
    volatile_store(vga_buffer, 0, VgaChar(65, 15))
    while true:
        pass
```
```
