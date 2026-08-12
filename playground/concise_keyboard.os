# Concise 4-Line Keyboard Driver in OS-Lang
@interrupt(33)
fn keyboard_handler():
    let key: int = inb(0x60)
    vga_write(0, 0, key as u8, 15)
    outb(0x20, 0x20)
