# Bare-Metal Cookbook — Chapter 1: The "Hello World" Bootloader

Welcome to the first practical implementation guide for OS-Lang. In this tutorial, we will write, compile, link, and boot a minimal x86_64 kernel stub that bypasses any host operating system and prints directly to the physical VGA text buffer.

By the end of this guide, you will see your custom language booting inside an emulated machine.

---

## 1. The Multiboot Bootstrap (`boot.s`)

To make our kernel bootable by industry-standard bootloaders like GRUB, we must define a **Multiboot 1 Header**. This header must be 32-bit aligned and contain specific magic numbers. 

Because a CPU starts in 32-bit Protected Mode when loaded by GRUB, we will use a tiny assembly file (`boot.s`) to satisfy Multiboot, set up a minimal stack, and hand off execution to our OS-Lang main entry point.

Create a file named `boot.s`:

```assembly
# Multiboot spec constants
.set MAGIC,    0x1BADB002
.set FLAGS,    0x00000003  # Align modules, provide memory map
.set CHECKSUM, -(MAGIC + FLAGS)

.section .multiboot
.align 4
.long MAGIC
.long FLAGS
.long CHECKSUM

.section .bss
.align 16
stack_bottom:
.skip 16384 # Allocate a 16KB stack space
stack_top:

.section .text
.global _start
_start:
    # Initialize stack pointer
    mov $stack_top, %esp

    # Call our OS-Lang main function
    call kernel_main

    # Fallback hang loop if kernel returns
_hang:
    cli
    hlt
    jmp _hang
```

---

## 2. The Kernel Entry Point (`main.os`)

Now we write our core logic in OS-Lang. We will declare a `hwmap` over the legacy VGA text memory plane (`0xB8000`) and iterate through a raw byte string to print "Hello from OS-Lang!" across the screen.

Create a file named `main.os`:

```os
# main.os - Core Entry Point

# Map the text-mode VGA frame buffer (80x25 characters)
# Each character is 2 bytes: Lower byte = ASCII, Upper byte = Color Attribute
hwmap VGABuffer at 0xB8000:
    video_memory: u16[2000]

# Define our mandatory panic handler required by the freestanding runtime
@no_mangle
def on_panic(file: ptr, line: u32, reason: ptr) -> !:
    @unsafe:
        # Paint the top-left corner red to indicate failure
        VGABuffer.video_memory[0] = 0x4F58 # Red background, White 'X'
        while True:
            pass

@no_mangle
def kernel_main():
    # 0x0F00 represents a White foreground text on a Black background
    var color_attr: u16 = 0x0F00
    
    # We use a raw fixed-size array for our message allocation
    var message: u8[19]
    message[0] = 72  # 'H'
    message[1] = 101 # 'e'
    message[2] = 108 # 'l'
    message[3] = 108 # 'l'
    message[4] = 111 # 'o'
    message[5] = 32  # ' '
    message[6] = 102 # 'f'
    message[7] = 114 # 'r'
    message[8] = 111 # 'o'
    message[9] = 109 # 'm'
    message[10] = 32 # ' '
    message[11] = 79 # 'O'
    message[12] = 83 # 'S'
    message[13] = 45 # '-'
    message[14] = 76 # 'L'
    message[15] = 97 # 'a'
    message[16] = 110 # 'n'
    message[17] = 103 # 'g'
    message[18] = 33 # '!'

    var i: usize = 0
    while i < 19:
        # Combine character byte and color byte into a unified 16-bit word
        var raw_char: u16 = message[i] as u16
        var vga_word: u16 = raw_char | color_attr
        
        # Write directly to the hardware map
        VGABuffer.video_memory[i] = vga_word
        i = i + 1
```

---

## 3. The Linker Script (`linker.ld`)

To prevent the compiler from placing our code segments at arbitrary virtual memory boundaries, we must use a linker script. This guarantees that GRUB can find our `.multiboot` header right at the physical `1MB` address mark.

Create a file named `linker.ld`:

```linker
ENTRY(_start)

SECTIONS
{
    /* GRUB looks for headers starting at the 1MB mark */
    . = 1M;

    .text BLOCK(4K) : ALIGN(4K)
    {
        *(.multiboot)
        *(.text)
    }

    .rodata BLOCK(4K) : ALIGN(4K)
    {
        *(.rodata)
    }

    .data BLOCK(4K) : ALIGN(4K)
    {
        *(.data)
    }

    .bss BLOCK(4K) : ALIGN(4K)
    {
        *(COMMON)
        *(.bss)
    }
}
```

---

## 4. The Compilation Pipeline

With your environment configured, execute the following chain of commands to build your source tree, link it against the layout boundaries, and execute the final image in the QEMU hardware emulator.

### Step 4.1: Compile the OS-Lang Frontend

```bash
osc main.os --target=x86_64-unknown-none --freestanding
```

> **NOTE:** This generates a freestanding `main.o` object file stripped clean of any host Linux/Windows dynamic hooks.

### Step 4.2: Assemble the Bootstrap Stub

```bash
as --32 boot.s -o boot.o
```

### Step 4.3: Link the Object Binaries

```bash
ld -m elf_i386 -T linker.ld boot.o main.o -o my_kernel.bin
```

### Step 4.4: Verify the Multiboot Header Validation

```bash
if grub-file --is-x86-multiboot my_kernel.bin; then
    echo "Success: Binary is verified Multiboot-compliant!"
else
    echo "Error: Binary fails Multiboot verification."
fi
```

### Step 4.5: Boot via QEMU Emulation

```bash
qemu-system-i386 -kernel my_kernel.bin
```

Your terminal will spin up an unmanaged hardware emulation plane, bypassing your standard desktop environment, and proudly output `Hello from OS-Lang!` on a crisp black screen.
