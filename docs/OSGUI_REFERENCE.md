# OS-Lang GUI System — OsGUI

**OsGUI** is a first-class GUI system built directly into the `os-lang` compiler. It lets you build beautiful, fully-featured desktop applications using the same clean, Pythonic `os-lang` syntax you already know — no HTML, no angle brackets, no web browser required.

---

## How It Works

OsGUI uses a **two-layer architecture**:

1. **Custom Syntax Layer** — You write declarative GUI code in `.os` files using clean, indentation-based blocks.
2. **Python Runtime Layer** — The compiler detects `guiapp` blocks and transpiles them to Python (Tkinter + customtkinter), giving you the full Python ecosystem for free.

```
┌─────────────────────────────────────────────────────────────────┐
│  You write:  guiapp, window, button, label, style, state, etc.  │
├─────────────────────────────────────────────────────────────────┤
│  Compiler:   Lexer → Parser → AST → GUI Transpiler              │
├─────────────────────────────────────────────────────────────────┤
│  Output:     Python + Tkinter script. Runs instantly.           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```os
guiapp HelloWorld:
    title: "Hello from OS-Lang!"
    width: 800
    height: 600
    background: "#1a1a2e"

    window Main:
        label greeting:
            text: "Welcome to OsGUI 🚀"
            color: "#e94560"
            font_size: 32
            x: 50
            y: 50

        button launch_btn:
            text: "Launch"
            bg: "#e94560"
            color: "#fff"
            x: 50
            y: 150
            width: 200
            height: 50
            on_click: handle_launch

    fn handle_launch() -> void:
        print("Launched!")
```

Run it:
```bash
osc myapp.os
```

---

## Elements Reference

### App & Structure
| Keyword | Description |
|---------|-------------|
| `guiapp` | Defines the entire application |
| `window` | A named screen/view |
| `page` | A routable page |
| `component` | A reusable UI component (like React components) |
| `router` | Multi-page routing config |

### Layout Containers
| Keyword | Description |
|---------|-------------|
| `panel` | Generic container (like `<div>`) |
| `scrollview` | Scrollable container |
| `tabs` | Tabbed panel |
| `accordion` | Collapsible sections |
| `card` | Styled card with shadow |
| `sidebar` | Fixed side panel |
| `navbar` | Top navigation bar |
| `statusbar` | Bottom status bar |
| `toolbar` | Icon action bar |
| `menubar` | Full application menu bar |

### Basic Elements
| Keyword | Description |
|---------|-------------|
| `label` | Static text display |
| `button` | Clickable button |
| `input` | Single-line text field |
| `textarea` | Multi-line text field |
| `image` | Display image from file/URL |
| `icon` | Icon by name |
| `link` | Clickable hyperlink text |
| `separator` | Horizontal/vertical rule |
| `spacer` | Invisible spacing |

### Form Elements
| Keyword | Description |
|---------|-------------|
| `checkbox` | Toggle checkbox |
| `radio` | Radio button |
| `dropdown` | Select dropdown |
| `slider` | Range slider |
| `toggle` | On/off switch |
| `spinbox` | Number input with arrows |
| `colorpicker` | Color picker dialog |
| `datepicker` | Calendar date picker |
| `filepicker` | File open dialog |

### Data Display
| Keyword | Description |
|---------|-------------|
| `table` | Sortable, filterable, paginated data table |
| `list` | Scrollable item list |
| `tree` | Collapsible tree view |
| `chart` | Line, bar, pie, donut, area, scatter chart |
| `progressbar` | Progress indicator |
| `spinner` | Loading animation |
| `badge` | Notification count badge |
| `avatar` | Circular image/initials |
| `tag` | Colored label chip |

### Drawing & Media
| Keyword | Description |
|---------|-------------|
| `canvas` | Free-draw 2D surface with full drawing API |
| `video` | Video player |
| `audio` | Audio player |

### Overlays & Dialogs
| Keyword | Description |
|---------|-------------|
| `modal` | Popup overlay dialog |
| `notification` | Toast/snackbar notification |
| `tooltip` | Hover tooltip |
| `popover` | Click-activated popup |
| `context_menu` | Right-click context menu |
| `alert_dialog` | Confirm/cancel dialog |
| `drag_zone` | Drag-and-drop source |
| `drop_zone` | Drag-and-drop target |

---

## Layout System

Set `layout:` on any container:

```os
panel main_layout:
    layout: flex          # flex | grid | stack | absolute
    direction: row        # row | column
    align: center         # start | center | end | stretch
    justify: space_between
    gap: 10
```

- **`flex`** — Flexbox row/column layout
- **`grid`** — CSS-style grid with `columns`, `rows`, `col_span`
- **`stack`** — Layers elements on top of each other (z-axis)
- **`absolute`** — Manual `x:` / `y:` coordinates

---

## Style System

### Inline styles
```os
button my_btn:
    bg: "#e94560"
    color: "#fff"
    border_radius: 8
    font_size: 14
    font_weight: bold
    shadow: true
    hover_bg: "#ff6b6b"
    active_scale: 0.97
```

### Named style blocks (like CSS classes)
```os
style PrimaryButton:
    bg: "#e94560"
    color: "#fff"
    border_radius: 8
    hover_bg: "#ff6b6b"
    active_bg: "#c73652"
    disabled_opacity: 0.5

button submit:
    text: "Submit"
    apply_style: PrimaryButton
```

### Global themes
```os
theme DarkMode:
    primary:    "#e94560"
    background: "#1a1a2e"
    surface:    "#16213e"
    text:       "#eaeaea"
    font:       "Inter"
    radius:     8

guiapp MyApp:
    apply_theme: DarkMode
```

---

## Reactive State

```os
guiapp Counter:
    state count: int = 0

    window Main:
        label display:
            text: count        # auto re-renders on change
            x: 100
            y: 100

        button inc_btn:
            text: "+1"
            x: 100
            y: 200
            on_click: increment

    fn increment() -> void:
        count = count + 1
```

---

## Custom Components

```os
component Card(title: str, body: str, accent: str = "#e94560"):
    render:
        panel root:
            layout: flex
            direction: column
            bg: "#16213e"
            border_radius: 12
            padding: 20

            label card_title:
                text: title
                color: accent
                font_size: 18

            label card_body:
                text: body

# Use it anywhere:
Card(title="Kernel Stats", body="CPU: 2% | RAM: 128MB")
```

---

## Events

```os
button my_btn:
    on_click:       handle_click
    on_double_click: handle_double
    on_right_click: show_context
    on_hover_enter: on_hover
    on_hover_leave: on_unhover
    on_focus:       on_focus
    on_blur:        on_blur

input search:
    on_change:  search_changed
    on_submit:  do_search

canvas drawing:
    on_mouse_down: start_draw
    on_mouse_move: draw_stroke
    on_mouse_up:   end_draw
    on_drop:       handle_file_drop
```

---

## Python Library Access

Use any Python library inside GUI functions with `@pylib`:

```os
@pylib("requests", "json")
fn fetch_users() -> void:
    response = requests.get("https://api.example.com/users")
    users_list = json.loads(response.text)

@pylib("PIL.Image", "tkinter.filedialog")
fn open_image() -> void:
    path = filedialog.askopenfilename()
    img = Image.open(path)
    viewer.set_image(img)

@pylib("matplotlib.pyplot")
fn plot_data() -> void:
    pyplot.plot([1, 2, 3], [4, 5, 6])
    pyplot.show()
```

---

## Animations

```os
animation FadeIn:
    from: opacity 0
    to:   opacity 1
    duration: 300ms
    easing: ease_out

label hero:
    text: "Hello!"
    animate_in:  FadeIn
    animate_out: SlideUp
    on_click_animation: pulse   # built-in: pulse, shake, bounce, wiggle
```

---

## Multi-Page Routing

```os
guiapp OSDesktop:
    router:
        home:     HomeScreen
        settings: SettingsScreen
    start: home

    navbar top_bar:
        menu:
            - label: "Home"      route: home
            - label: "Settings"  route: settings

page HomeScreen:
    window:
        label welcome:
            text: "Welcome!"

page SettingsScreen:
    window:
        toggle dark_mode:
            label: "Dark Mode"
            bind: dark_mode_enabled
```

---

## Charts

```os
chart cpu_chart:
    type: line       # line | bar | pie | donut | area | scatter
    width: 400
    height: 200
    data: cpu_history
    labels: time_labels
    color: "#e94560"
    fill: true
    smooth: true
```

---

## Tables

```os
table users_table:
    columns:
        - name: "Name"   key: "name"   sortable: true
        - name: "Email"  key: "email"
        - name: "Role"   key: "role"   filterable: true
    data: users_list
    searchable: true
    paginate: 20
    striped: true
```

---

## Canvas & 2D Drawing

```os
canvas game_canvas:
    width: 800
    height: 600
    bg: "#000"
    on_ready: draw_scene

fn draw_scene(ctx: Canvas) -> void:
    ctx.fill_rect(0, 0, 100, 100, "#e94560")
    ctx.fill_circle(400, 300, 50, "#00d2ff")
    ctx.draw_text("Hello!", x=100, y=100, font_size=24, color="#fff")
    ctx.draw_image("sprite.png", x=200, y=200, width=64, height=64)
```

---

## Menus

```os
menubar app_menu:
    menu File:
        item "New File"   shortcut: "Ctrl+N"  on_click: new_file
        item "Open..."    shortcut: "Ctrl+O"  on_click: open_file
        separator
        item "Exit"       shortcut: "Alt+F4"  on_click: quit_app
    menu Edit:
        item "Undo"       shortcut: "Ctrl+Z"  on_click: undo

context_menu element_ctx:
    item "Cut"     on_click: cut
    item "Copy"    on_click: copy
    item "Paste"   on_click: paste
```

---

## Notifications & Dialogs

```os
notification task_done:
    message: "Compiled successfully!"
    type: success      # success | error | warning | info
    duration: 3000ms
    position: top_right

modal confirm_dialog:
    title: "Confirm"
    message: "Are you sure?"
    buttons:
        - text: "Cancel"   on_click: close_dialog  style: secondary
        - text: "Confirm"  on_click: do_action      style: primary_danger
```
