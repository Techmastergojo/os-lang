# Concise Mouse Cursor Renderer in OS-Lang
@unsafe
fn update_cursor(x: int, y: int):
    draw_cursor(x, y, 14)
    vga_write(x + 1, y, 77 as u8, 14) # 'M' character
