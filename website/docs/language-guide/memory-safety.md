# Memory Safety & `@unsafe`

Because OS-Lang allows direct hardware manipulation, it enforces strict boundaries to prevent memory corruption in high-level business logic. All direct memory access via pointers **must** reside within an `@unsafe:` block.

### Example: Writing to the VGA Buffer

```os-lang
fn main() -> int:
    let mut address: int = 0xB8000
    let mut vga_buffer: *mut u16 = address as *mut u16
    
    # Safely guarded raw memory access
    @unsafe:
        let val: u16 = *vga_buffer
        *vga_buffer = 0x0F41  # Write 'A' (white on black) to the screen
        
    return 0
```
