# OS-Lang: A Next-Generation Language for Bare-Metal Development

[![PyPI version](https://badge.fury.io/py/os-lang.svg)](https://badge.fury.io/py/os-lang)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OS-Lang (`.os`)** is a brand new, highly-opinionated programming language specifically designed for writing bare-metal operating systems, kernels, low-level system software — fully-featured desktop GUIs, and now a **first-class plugin/extension architecture (LEX)**.

It combines the clean, fast, indentation-based syntax of Python with the raw, bare-metal memory control of C and Rust, **plus** a built-in GUI system (OsGUI) and a kernel-level extension framework.

## Why OS-Lang?
When building an operating system, a language must compile directly to bare-metal machine code, manage raw memory addresses manually, and interface with hardware without relying on an underlying OS or garbage collector. OS-Lang achieves this seamlessly by compiling directly to **LLVM IR**.

- **Pythonic Syntax**: No semicolons, no curly braces, strict indentation.
- **Bare-Metal Compilation**: Compiles directly to object files (`.o`) via LLVM.
- **No Runtime/Garbage Collector**: You have 100% control over memory.
- **Hardware Maps (`hwmap`)**: A powerful paradigm for mapping C-style structs directly to volatile hardware memory registers.
- **Intrinsic OS Support**: First-class support for `volatile_load`, `volatile_store`, and CPU intrinsics.
- **Explicit Safety (`@unsafe`)**: Hardware manipulation is strictly guarded by explicit unsafe scopes.
- 🆕 **OsGUI**: A full GUI system — build desktop apps using `guiapp`, `window`, `button`, `state`, and more. Like HTML+CSS+React, but in `.os` syntax.
- 🆕 **LEX**: Leopard Extension System — write OS extensions with zero boilerplate using `@override`, `@hook`, `@meta` decorators.

## Installation

OS-Lang is available on the global Python Package Index (PyPI). You can install it instantly:

```bash
pip install os-lang
```

## Quick Start

### Bare-Metal Kernel

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

---

## 🆕 Leopard Extension System (LEX)

LEX is a **zero-overhead, kernel-level extension architecture** built into the OS-Lang compiler. You can dynamically override OS functions and inject metadata without touching a single line of the core kernel code.

### How It Works

Extensions are `.osext` files (same syntax as `.os`). The compiler reads the `@extend`, `@override`, `@hook`, and `@meta` decorators and automatically emits an ELF metadata entry into the `.osext_meta` section. At boot, the OS kernel scans this section and wires up the hooks automatically.

```
┌─────────────────────────────────────────────────────────────┐
│  You write: my_theme.osext (with @override decorator)       │
├─────────────────────────────────────────────────────────────┤
│  osc compiles → .osext_meta ELF section with hook metadata  │
├─────────────────────────────────────────────────────────────┤
│  Kernel boot → scans .osext_meta → wires function pointers  │
├─────────────────────────────────────────────────────────────┤
│  Runtime: your extension fn is called instead of original   │
└─────────────────────────────────────────────────────────────┘
```

### Writing a LEX Extension

```python
# my_theme.osext
@meta(author="Hamza", version="1.0.0", description="Red Cursor Theme")
@extend

@override(target="draw_mouse_cursor")
@unsafe
fn custom_mouse_cursor(x: int, y: int) -> void:
    # Draw a custom red block cursor
    let vga: int = 0xB8000 + (y / 16 * 80 + x / 8) * 2
    let p: ptr[u8] = vga as ptr[u8]
    *p = 219 as u8      # █ character
    let cp: ptr[u8] = (vga + 1) as ptr[u8]
    *cp = 196 as u8     # Red on black
```

Compile it:
```bash
osc my_theme.osext
```

That's it. One file, zero boilerplate.

### Available LEX Decorators

| Decorator | Purpose |
|---|---|
| `@extend` | Marks a file as a LEX extension module |
| `@meta(author, version, description)` | Metadata embedded into the ELF binary |
| `@override(target="fn_name")` | Replace an existing OS function at runtime |
| `@hook(target="fn_name", type="before"\|"after")` | Inject code before/after a function |
| `@new` | Add a completely new function to the OS at runtime |
| `@app` | Register an extension as a full application |
| `@service` | Register an extension as a background service |

---

## 🆕 Testing LEX Extensions on the Real Kernel

We believe that **failing is part of testing**. Instead of using fake sandboxes, you test your `.osext` extensions directly against the real Leopard OS kernel.

### 1. Compile Your Extension
Compile your `.osext` file into an object (`.o`) file using the OS-Lang compiler:
```bash
osc extensions/my_theme.osext
```
This produces `extensions/my_theme.o`.

### 2. Link with the Real Kernel
Link your new extension object file together with the rest of the Leopard OS kernel objects into a final ELF binary, and convert it to a flat binary:
```bash
# Note: Requires WSL with binutils installed (wsl sudo apt install binutils)
wsl bash -c "ld -T linker.ld -o kernel.elf boot.o src/*.o extensions/*.o"
wsl bash -c "objcopy -O binary kernel.elf kernel.bin"
```

### 3. Boot and Test in QEMU
Boot the newly linked `kernel.bin` in QEMU to see your extension live:
```bash
qemu-system-x86_64 -kernel kernel.bin -m 256M -vga std -smp 2 -drive id=disk,file=disk.img,format=raw,if=none -device ahci,id=ahci -device ide-hd,drive=disk,bus=ahci.0 -device qemu-xhci,id=xhci -device usb-mouse,bus=xhci.0 -device usb-kbd,bus=xhci.0
```

### What Happens
1. The kernel boots up normally.
2. During initialization, the kernel scans the `.osext_meta` section populated by your extensions.
3. Your `@override` hooks are instantly wired up, replacing the default kernel functions.
4. If your extension crashes, the real kernel crashes! Debug it, fix your OS-Lang code, recompile, link, and try again.

---

## 🆕 GUI App (OsGUI)

Create a desktop GUI app in the same `.os` syntax:

```python
# myapp.os
guiapp MyApp:
    title: "My OS Desktop"
    width: 800
    height: 600
    background: "#1a1a2e"
    apply_theme: DarkMode

    state count: int = 0

    window Main:
        label title_text:
            text: "OS-Lang GUI"
            color: "#e94560"
            font_size: 32
            x: 50
            y: 40

        button inc_btn:
            text: "+ Increment"
            bg: "#e94560"
            on_click: increment

    fn increment() -> void:
        count = count + 1

theme DarkMode:
    primary:    "#e94560"
    background: "#1a1a2e"
    text:       "#eaeaea"
    font:       "Inter"
```

Run it:
```bash
osc myapp.os
```

## OsGUI — Full Feature Set

OsGUI gives you everything you need to build real desktop apps:

| Feature | Details |
|---|---|
| **60+ Element Types** | label, button, input, checkbox, dropdown, slider, table, chart, canvas, video, modal, tooltip, and more |
| **Layout Engines** | Flex, Grid, Stack, Absolute |
| **CSS-like Styles** | Named style blocks, global themes, hover/active/focus/disabled states |
| **Animations** | FadeIn, SlideUp, Bounce, custom — with easing controls |
| **Reactive State** | `state` keyword — changes trigger automatic re-renders |
| **Custom Components** | `component Card(title: str):` — reusable, parameterized widgets |
| **Multi-Page Routing** | `router:` + `page` declarations, navbar integration |
| **Menus** | `menubar`, `context_menu`, keyboard shortcuts |
| **Dialogs** | `modal`, `notification` toast, `alert_dialog`, `tooltip` |
| **Canvas** | Full 2D drawing API — rects, circles, text, images, polygons |
| **Charts** | Line, bar, pie, donut, area, scatter — powered by matplotlib |
| **Data Tables** | Sortable, filterable, paginated, with search |
| **Drag & Drop** | `drag_zone` and `drop_zone` elements |
| **Python Libs** | `@pylib("requests", "PIL.Image")` — use any Python package inside GUI functions |

See the full **[OsGUI Reference](docs/OSGUI_REFERENCE.md)** for complete syntax and examples.

## Documentation

See the `docs/` directory for full documentation:
- **[Language Reference](docs/LANGUAGE_REFERENCE.md)**: Syntax, Types, and Primitives.
- **[OsGUI Reference](docs/OSGUI_REFERENCE.md)**: 🆕 Full GUI system — elements, layout, styles, state, events, and more.
- **[Language Specification](docs/LANGUAGE_SPECIFICATION.md)**: Full compiler spec.
- **[Bare-Metal Cookbook](docs/BARE_METAL_COOKBOOK.md)**: Recipes for OS development.
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

It combines the clean, fast, indentation-based syntax of Python with the raw, bare-metal memory control of C and Rust, **plus** a built-in GUI system (OsGUI) inspired by HTML, CSS, and React.

## Why OS-Lang?
When building an operating system, a language must compile directly to bare-metal machine code, manage raw memory addresses manually, and interface with hardware without relying on an underlying OS or garbage collector. OS-Lang achieves this seamlessly by compiling directly to **LLVM IR**.

- **Pythonic Syntax**: No semicolons, no curly braces, strict indentation.
- **Bare-Metal Compilation**: Compiles directly to object files (`.o`) via LLVM.
- **No Runtime/Garbage Collector**: You have 100% control over memory.
- **Hardware Maps (`hwmap`)**: A powerful paradigm for mapping C-style structs directly to volatile hardware memory registers.
- **Intrinsic OS Support**: First-class support for `volatile_load`, `volatile_store`, and CPU intrinsics.
- **Explicit Safety (`@unsafe`)**: Hardware manipulation is strictly guarded by explicit unsafe scopes.
- 🆕 **OsGUI**: A full GUI system — build desktop apps using `guiapp`, `window`, `button`, `state`, and more. Like HTML+CSS+React, but in `.os` syntax.

## Installation

OS-Lang is available on the global Python Package Index (PyPI). You can install it instantly:

```bash
pip install os-lang
```

## Quick Start

### Bare-Metal Kernel

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

### 🆕 Leopard Extension System (LEX)

OS-Lang now supports a **zero-overhead, kernel-level extension architecture** called LEX. You can dynamically override OS functions and inject metadata without touching the core kernel code.

```python
# my_extension.osext
@meta(author="Hamza", version="1.0.0", description="My Theme")
@extend

@override(target="draw_mouse_cursor")
@unsafe
fn custom_mouse(x: int, y: int) -> void:
    # Your custom cursor logic here
    pass
```
The compiler automatically emits this metadata into a special `.osext_meta` ELF section for the kernel to read at boot!

### 🆕 GUI App (OsGUI)

Create a desktop GUI app in the same `.os` syntax:

```python
# myapp.os
guiapp MyApp:
    title: "My OS Desktop"
    width: 800
    height: 600
    background: "#1a1a2e"
    apply_theme: DarkMode

    state count: int = 0

    window Main:
        label title_text:
            text: "OS-Lang GUI"
            color: "#e94560"
            font_size: 32
            x: 50
            y: 40

        label counter_display:
            text: count
            font_size: 48
            x: 50
            y: 150

        button inc_btn:
            text: "+ Increment"
            bg: "#e94560"
            color: "#fff"
            border_radius: 8
            x: 50
            y: 250
            width: 180
            height: 50
            on_click: increment

    fn increment() -> void:
        count = count + 1

theme DarkMode:
    primary:    "#e94560"
    background: "#1a1a2e"
    text:       "#eaeaea"
    font:       "Inter"
```

Run it:
```bash
osc myapp.os
```

A window appears instantly — no extra framework needed! 🚀

Or, use the **Desktop GUI App**:
```bash
osc-gui
```

## OsGUI — Full Feature Set

OsGUI gives you everything you need to build real desktop apps:

| Feature | Details |
|---|---|
| **60+ Element Types** | label, button, input, checkbox, dropdown, slider, table, chart, canvas, video, modal, tooltip, and more |
| **Layout Engines** | Flex, Grid, Stack, Absolute |
| **CSS-like Styles** | Named style blocks, global themes, hover/active/focus/disabled states |
| **Animations** | FadeIn, SlideUp, Bounce, custom — with easing controls |
| **Reactive State** | `state` keyword — changes trigger automatic re-renders |
| **Custom Components** | `component Card(title: str):` — reusable, parameterized widgets |
| **Multi-Page Routing** | `router:` + `page` declarations, navbar integration |
| **Menus** | `menubar`, `context_menu`, keyboard shortcuts |
| **Dialogs** | `modal`, `notification` toast, `alert_dialog`, `tooltip` |
| **Canvas** | Full 2D drawing API — rects, circles, text, images, polygons |
| **Charts** | Line, bar, pie, donut, area, scatter — powered by matplotlib |
| **Data Tables** | Sortable, filterable, paginated, with search |
| **Drag & Drop** | `drag_zone` and `drop_zone` elements |
| **Python Libs** | `@pylib("requests", "PIL.Image")` — use any Python package inside GUI functions |

See the full **[OsGUI Reference](docs/OSGUI_REFERENCE.md)** for complete syntax and examples.

## Documentation

See the `docs/` directory for full documentation:
- **[Language Reference](docs/LANGUAGE_REFERENCE.md)**: Syntax, Types, and Primitives.
- **[OsGUI Reference](docs/OSGUI_REFERENCE.md)**: 🆕 Full GUI system — elements, layout, styles, state, events, and more.
- **[Language Specification](docs/LANGUAGE_SPECIFICATION.md)**: Full compiler spec.
- **[Bare-Metal Cookbook](docs/BARE_METAL_COOKBOOK.md)**: Recipes for OS development.
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
