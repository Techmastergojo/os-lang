@interrupt(33)
fn handle_keyboard():
    let x = 1

@unsafe
fn vga_print():
    let mut vga: ptr[u8] = 753664
    vga = 72
