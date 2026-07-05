# Hardware Alignment (`@packed`)

When mapping structs directly to hardware memory (e.g., GDT entries or IDT descriptors), LLVM padding can corrupt the layout.

Use the `@packed` decorator to enforce zero-padding.

```os-lang
@packed
struct IdtEntry {
    offset_low: u16
    selector: u16
    ist: u8
    type_attr: u8
    offset_mid: u16
    offset_high: u32
    zero: u32
}

fn initialize_idt() -> void:
    # sizeof() calculates byte-width at compile time
    let entry_size: int = sizeof(IdtEntry)
    print(entry_size) # Outputs exactly 16 bytes!
```
