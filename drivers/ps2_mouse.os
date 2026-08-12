# PS/2 Mouse Driver in OS-Lang
hwmap MouseState:
    x: i32
    y: i32
    left_button: u8
    right_button: u8

let mut mouse_x: int = 40
let mut mouse_y: int = 12

@driver
fn ps2_mouse_init():
    # Enable auxiliary device
    outb(0x64, 0xA8)
    # Enable interrupts
    outb(0x64, 0x20)
    let status: u8 = (((inb(0x60) as int) | 2)) as u8
    outb(0x64, 0x60)
    outb(0x60, status as int)

@interrupt(44)
fn ps2_mouse_isr():
    let status: u8 = inb(0x64)
    if ((status as int) & 1) != 0:
        let data: int = inb(0x60) as int
        # Render cursor on screen
        draw_cursor(mouse_x, mouse_y, 14)
    outb(0x20, 0x20)
    outb(0xA0, 0x20)
