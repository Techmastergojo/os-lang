# 🚀 OS-Lang v2.0 Release & GitHub Guide

Welcome to the major **OS-Lang v2.0** update! This release transforms OS-Lang into the ultimate bare-metal development language, introducing **Web-Style OsGUI Layouts**, **Actionable AI Compiler Diagnostics**, **Built-in Hardware Intrinsics**, and **Multi-Target Cross-Compilation superpowers**.

---

## 🌟 What's New in Version 2.0

### 1. 🌐 Web-Style Semantic OsGUI Layout Engine
Forget hardcoded X/Y pixel math. You can now build bare-metal desktop GUIs using web-like semantic containers and Flexbox/Grid alignment:

```python
guiapp LeopardDesktop:
    title: "Leopard OS"
    width: 1024
    height: 768
    background: "#0f0f1a"

    window Main:
        header TopNav:
            align: center
            justify: space_between
            bg: "#161625"
            height: 50

            label logo:
                text: "Leopard OS"
                color: "#ff0055"

        container ContentBody:
            direction: row
            flex: 1

            sidebar LeftPanel:
                width: 220
                bg: "#1a1a2e"

                button btn_files:
                    text: "📁 Files"

            main Workspace:
                flex: 1
                align: center
                justify: center

                card WelcomeCard:
                    width: 400
                    height: 200

                    label msg:
                        text: "Welcome to Bare-Metal Web Desktop!"

        footer Status:
            height: 30
            align: center
            label txt:
                text: "System Ready"
```

#### New Layout Constructs:
- **Semantic Sections**: `header`, `footer`, `main`, `sidebar`, `nav`, `section`, `container`, `card`, `panel`, `row`, `col`.
- **Flexbox Properties**: `direction` (`row`|`column`), `align` (`center`|`start`|`end`|`stretch`), `justify` (`space_between`|`space_around`|`center`), `gap`, `flex`.

---

### 🤖 2. LLM / AI Integration & Actionable Compiler Hints
- **`LLM_RULES.md`**: Complete specification file for AI assistants (Cursor, Copilot, ChatGPT, Claude, Gemini).
- **Actionable Hints**: If an AI assistant generates invalid syntax, the compiler gives explicit instructions:
  - `def` keyword -> `"Hint: OS-Lang uses 'fn' for function definitions."`
  - `var`/`const` -> `"Hint: Variable declarations must use 'let' or 'let mut'."`
  - Pointer access outside `@unsafe` -> `"Hint: Must be inside an @unsafe function or block."`

---

### ⚡ 3. Ergonomic Hardware Intrinsics (4-Line Drivers)
You no longer need long pointer casting chains to write VGA text or render graphics:

- `vga_write(x, y, char, color)`: 1-line VGA text buffer drawing.
- `draw_cursor(x, y, color)`: 1-line mouse cursor block.
- `draw_pixel(x, y, color)`: 1-line LFB pixel drawing.
- `inb(port)`, `outb(port, val)`, `inw(port)`, `outw(port, val)`, `cli()`, `sti()`, `halt()`.

#### 4-Line Keyboard Handler Example:
```python
@interrupt(33)
fn keyboard_handler():
    let key: int = inb(0x60)
    vga_write(0, 0, key as u8, 15)
    outb(0x20, 0x20)
```

---

### 🛠️ 4. `osc` CLI Superpowers
- **Multi-Target Cross-Compilation**:
  ```bash
  python -m src.main kernel.os --target x86_64
  python -m src.main kernel.os --target arm64
  python -m src.main kernel.os --target riscv64
  ```
- **1-Click QEMU Emulator Runner**:
  ```bash
  python -m src.main kernel.os --run-qemu
  ```
- **AI Driver Generator**:
  ```bash
  python -m src.main --ai-driver "RTL8139 NIC"
  ```
- **C Header Import Syntax**:
  ```python
  import_c "pci.h"
  ```

---

## 📦 How to Commit & Push to GitHub

Run these commands in your workspace to push all new features to your repository:

```bash
# 1. Stage all new and modified files
git add .

# 2. Commit with clean release message
git commit -m "feat: OS-Lang v2.0 - Web OsGUI Layout Engine, AI Compiler Hints, Driver Intrinsics & CLI Superpowers"

# 3. Push to main branch
git push origin main
```

---

## 🧪 Test Suite Verification
All 135 unit & integration tests pass with 100% success rate:
```bash
pytest
```
