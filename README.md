# OS-Lang: A Next-Generation Language for Bare-Metal Development

[![PyPI version](https://badge.fury.io/py/os-lang.svg)](https://badge.fury.io/py/os-lang)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**OS-Lang (`.os`)** is a brand new, highly-opinionated programming language specifically designed for writing bare-metal operating systems, kernels, low-level system software — and now **fully-featured desktop GUIs**.

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
