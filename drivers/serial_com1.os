# Serial UART COM1 Logging Driver in OS-Lang
@driver
fn serial_com1_init():
    outb(0x3F8 + 1, 0x00)    # Disable interrupts
    outb(0x3F8 + 3, 0x80)    # Enable DLAB (set baud rate divisor)
    outb(0x3F8 + 0, 0x03)    # Set divisor to 3 (lo byte) 38400 baud
    outb(0x3F8 + 1, 0x00)    # (hi byte)
    outb(0x3F8 + 3, 0x03)    # 8 bits, no parity, one stop bit
    outb(0x3F8 + 2, 0xC7)    # Enable FIFO, clear with 14-byte threshold
    outb(0x3F8 + 4, 0x0B)    # IRQs enabled, RTS/DSR set

@unsafe
fn serial_write_char(ch: u8):
    while (((inb(0x3F8 + 5) as int) & 0x20)) == 0:
        pass
    outb(0x3F8, ch as int)

@unsafe
fn serial_print(msg: str):
    serial_write_char(79 as u8) # 'O'
    serial_write_char(83 as u8) # 'S'
