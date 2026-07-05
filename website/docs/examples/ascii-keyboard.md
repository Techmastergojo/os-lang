# Creating an ASCII Keyboard Driver

This example demonstrates how to read scan codes from the PS/2 keyboard port, handle the hardware interrupt, and map scancodes to ASCII characters using pattern matching.

### 1. The Port I/O Setup

We use OS-Lang's built-in `inb()` and `outb()` hardware intrinsics to talk to the keyboard controller (Port `0x60`) and the Programmable Interrupt Controller (PIC at `0x20`).

### 2. The Implementation

```os-lang
# Global Scancode to ASCII Mapper
fn map_scancode_to_ascii(scancode: u8) -> u8:
    match scancode:
        0x1E =>: # 'A'
            return 65
        0x30 =>: # 'B'
            return 66
        0x2E =>: # 'C'
            return 67
        _ =>:
            return 0 # Unknown key

# The Hardware Interrupt Handler (IRQ 1 for Keyboard)
@interrupt(33)
fn keyboard_interrupt_handler() -> void:
    # 1. Read the scancode from PS/2 Port 0x60
    let scancode: u8 = inb(0x60)
    
    # 2. Only process key-down events (top bit is 0)
    if scancode < 0x80:
        let ascii_char: u8 = map_scancode_to_ascii(scancode)
        if ascii_char != 0:
            print_char(ascii_char)
            
    # 3. Send End of Interrupt (EOI) to the PIC so it sends more interrupts
    outb(0x20, 0x20)
```

### Explanation

1. **`@interrupt(33)`**: This decorator tells the OS-Lang compiler to apply the `x86_intrcc` calling convention, ensuring all CPU registers are safely pushed before execution and popped before sending the `iretq` instruction.
2. **`inb(0x60)`**: This compiler intrinsic reads a single byte from the hardware port.
3. **`outb(0x20, 0x20)`**: Acknowledges the interrupt to the PIC. If you forget this, your keyboard will only work once!
