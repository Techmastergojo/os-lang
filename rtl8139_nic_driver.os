# Generated AI Driver for RTL8139 NIC in OS-Lang
@driver
fn init_rtl8139_nic_driver():
    # Write initialization command to primary I/O port
    outb(0x3F8, 0x00)
    let mut status: u8 = inb(0x3F8) as u8
    vga_write(0, 0, status, 15)

@interrupt(33)
fn rtl8139_nic_isr_handler():
    let data: int = inb(0x60)
    vga_write(0, 1, data as u8, 14)
    outb(0x20, 0x20)
