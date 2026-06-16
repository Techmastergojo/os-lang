# The OS-Lang Bare-Metal Cookbook

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


# Bare-Metal Cookbook — Chapter 2: The Interrupt Descriptor Table (IDT)

Welcome to Chapter 2. Now that we have successfully booted OS-Lang and printed to the screen, we must handle the inevitable: hardware interrupts and CPU exceptions.

If a division-by-zero occurs or a keyboard key is pressed, the CPU halts normal execution and searches for an **Interrupt Descriptor Table (IDT)**. If it cannot find one, it crashes into a fatal "triple fault."

In this chapter, we will use OS-Lang's `@packed` structures, inline assembly, and `hwmap` capabilities to build a functioning IDT and catch our first hardware exception.

---

## 1. The Theory: What is an IDT?

An Interrupt Descriptor Table is exactly what it sounds like: a table (array) in memory that acts as a directory. It contains 256 entries. Each entry tells the CPU: "If interrupt *N* happens, jump to this specific memory address and run the handler code."

*   **Exceptions (0-31):** CPU-generated errors (e.g., Page Fault, Divide by Zero).
*   **Hardware Interrupts (32-255):** External signals from devices (e.g., Keyboard, Mouse, System Timers).

---

## 2. Modeling the Hardware in OS-Lang

The CPU demands a very strict byte-layout for each IDT entry. It cannot have compiler-added padding. We use OS-Lang's `@packed` decorator to enforce an exact 8-byte layout (in 32-bit mode) or 16-byte layout (in 64-bit mode). Here we will define the 32-bit x86 layout.

Create a file named `idt.os`:

```os
# idt.os

# Define the exact layout of a single IDT Gate
@packed
struct IDTEntry:
    offset_low: u16      # Lower 16 bits of handler function address
    selector: u16        # Kernel segment selector
    zero: u8             # Unused, must be zero
    type_attr: u8        # Type and Attributes flags (e.g., Present, Ring 0)
    offset_high: u16     # Higher 16 bits of handler function address

# Define the pointer structure required by the `lidt` instruction
@packed
struct IDTPointer:
    limit: u16           # Size of the entire IDT array minus 1
    base: ptr            # Memory address of the first IDTEntry
```

Now, we instantiate an array of 256 entries and configure our pointer:

```os
# Allocate a global array of 256 entries
var idt_entries: IDTEntry[256]
var idtp: IDTPointer
```

---

## 3. Writing the Interrupt Handlers

When an interrupt fires, the CPU doesn't follow normal C-style function calling conventions. It blindly jumps to the handler. 

If our compiler added a standard function prologue (modifying the stack and base pointers), it would corrupt the CPU's state. To prevent this, we declare our handlers with `@naked`. We must manually save the CPU state, handle the error, restore the state, and use the special `iret` (interrupt return) instruction.

```os
# A handler for Exception 0: Divide by Zero
@naked
def divide_by_zero_handler():
    @unsafe:
        # Save all general-purpose registers
        asm("pushal")
        
    # In a real OS, you would print a panic message here
    on_panic("idt.os", 42, "Divide by Zero Exception Caught!")
    
    @unsafe:
        # Restore registers and return from interrupt
        asm("popal")
        asm("iret")
```

---

## 4. Registering the IDT with the CPU

Finally, we need a function to dynamically populate our `idt_entries` array and tell the CPU where to find it using the `lidt` (Load IDT) instruction via inline assembly.

```os
def set_idt_gate(num: u8, handler_addr: usize, selector: u16, flags: u8):
    # Extract the low and high 16-bits of the address
    var offset_low: u16 = (handler_addr & 0xFFFF) as u16
    var offset_high: u16 = ((handler_addr >> 16) & 0xFFFF) as u16
    
    idt_entries[num].offset_low = offset_low
    idt_entries[num].selector = selector
    idt_entries[num].zero = 0
    idt_entries[num].type_attr = flags
    idt_entries[num].offset_high = offset_high

def init_idt():
    # Setup the IDT pointer
    # Size is (256 * 8) - 1 = 2047
    idtp.limit = 2047
    
    @unsafe:
        # Cast the array reference to a raw pointer
        idtp.base = idt_entries as ptr

    # Register Exception 0 (Divide by Zero)
    # 0x08 is the code segment selector, 0x8E means a 32-bit Interrupt Gate
    var handler_ptr: usize = divide_by_zero_handler as usize
    set_idt_gate(0, handler_ptr, 0x08, 0x8E)

    # Load the IDT into the CPU
    @unsafe:
        # The 'lidt' instruction takes the memory address of our IDTPointer
        var idtp_addr: ptr = idtp as ptr
        asm("lidt (%0)" : : "r"(idtp_addr) : "memory")
        
        # Enable interrupts globally
        asm("sti")
```

With `init_idt()` called right after `kernel_main()` boots, your OS-Lang kernel is officially ready to catch exceptions and handle hardware events asynchronously!


---

# Bare-Metal Cookbook — Chapter 3: Hardware I/O & The Keyboard Driver

With the Interrupt Descriptor Table (IDT) actively catching exceptions, we can now interact with external hardware. The most fundamental piece of hardware for a developer is the keyboard.

In x86 architecture, the CPU talks to legacy devices like the keyboard via **I/O Ports**. This is a separate address space from standard RAM, requiring special assembly instructions: `in` to read data, and `out` to send data.

In this chapter, we will build a basic Programmable Interrupt Controller (PIC) interface, map the keyboard interrupt (IRQ 1), and read a scancode when a key is pressed.

---

## 1. Port Communication (`inb` and `outb`)

Because OS-Lang allows inline assembly via `@unsafe` blocks, we can easily create wrapper functions to talk to hardware ports.

Create a file named `io.os`:

```os
# io.os

# Write a single byte to the specified hardware port
def outb(port: u16, data: u8):
    @unsafe:
        asm("outb %0, %1" : : "a"(data), "Nd"(port))

# Read a single byte from the specified hardware port
def inb(port: u16) -> u8:
    var result: u8 = 0
    @unsafe:
        asm("inb %1, %0" : "=a"(result) : "Nd"(port))
    return result
```

---

## 2. Acknowledging the PIC

When a hardware device fires an interrupt, the Programmable Interrupt Controller (PIC) routes it to the CPU. If we don't explicitly tell the PIC "I have handled this interrupt," it will stop sending future interrupts.

```os
# The master PIC uses ports 0x20 (command) and 0x21 (data)
def pic_acknowledge():
    # 0x20 is the End of Interrupt (EOI) command
    outb(0x20, 0x20)
```

---

## 3. The Keyboard Interrupt Handler (IRQ 1)

The keyboard is hardwired to IRQ 1. Depending on how you remap the PIC (typically, IRQs 0-15 are mapped to IDT entries 32-47), the keyboard will trigger IDT Entry 33.

When a key is pressed, its scancode is placed on I/O port `0x60`.

Create a file named `keyboard.os`:

```os
# keyboard.os

# Our global cursor tracker for the VGA buffer
var cursor_x: usize = 0
var cursor_y: usize = 0

@naked
def keyboard_handler():
    @unsafe:
        asm("pushal")
    
    # Read the scancode from the keyboard data port
    var scancode: u8 = inb(0x60)
    
    # Handle key press (top bit is 0 for key down, 1 for key up)
    if (scancode & 0x80) == 0:
        # For simplicity, we just print a 'K' to show a key was pressed
        # In a real OS, you'd map the scancode to an ASCII character array
        var color_attr: u16 = 0x0F00 # White on black
        var char_word: u16 = 75 | color_attr # 75 is ASCII 'K'
        
        # Calculate VGA index: (y * 80) + x
        var index: usize = (cursor_y * 80) + cursor_x
        VGABuffer.video_memory[index] = char_word
        
        cursor_x = cursor_x + 1
        if cursor_x >= 80:
            cursor_x = 0
            cursor_y = cursor_y + 1

    # We must acknowledge the interrupt so the keyboard keeps working!
    pic_acknowledge()
    
    @unsafe:
        asm("popal")
        asm("iret")
```

---

## 4. Hooking it all together

Back in our `init_idt()` function from Chapter 2, we just need to register our new keyboard handler to IDT entry 33.

```os
    # ... inside init_idt() ...
    
    # Register the Keyboard Handler to IDT 33
    var kbd_ptr: usize = keyboard_handler as usize
    set_idt_gate(33, kbd_ptr, 0x08, 0x8E)
```

With this in place, your OS-Lang kernel is now fully interactive. When you run `qemu`, every key press will immediately echo a 'K' directly onto the screen via a hardware-triggered interrupt!


---

# Bare-Metal Cookbook — Chapter 4: Memory Management & Paging

In a bare-metal environment, memory is a raw sequence of bytes. To protect the kernel, isolate processes, and prevent fragmentation, an operating system must implement **Paging**. Paging breaks physical memory into fixed-size chunks (typically 4KB) and maps them to virtual addresses.

This chapter walks through building a basic Page Directory and enabling paging in OS-Lang.

---

## 1. The Paging Data Structures

x86 architecture uses a two-tier paging system in 32-bit mode: a Page Directory (PD) containing 1024 Page Directory Entries (PDEs), which point to Page Tables (PTs), which in turn contain 1024 Page Table Entries (PTEs). Each maps 4KB.

We use OS-Lang's `@packed` and arrays to model this exact 4KB-aligned layout.

Create a file named `paging.os`:

```os
# paging.os

# Define a Page Table Entry (PTE)
# The CPU expects a 32-bit integer where the upper 20 bits are the physical frame address, 
# and the lower 12 bits are flags (Present, Read/Write, User/Supervisor, etc.)
var PAGE_PRESENT: u32 = 0x1
var PAGE_RW: u32 = 0x2
var PAGE_USER: u32 = 0x4

# Define arrays for the Page Directory and the first Page Table.
# We align them to 4096 bytes (4KB) as strictly required by the CPU.
@align(4096)
var page_directory: u32[1024]

@align(4096)
var first_page_table: u32[1024]
```

---

## 2. Initializing the Page Table

Before enabling paging, we must identity-map the first 4 Megabytes of memory so our kernel (which is executing at 1MB) does not instantly crash when virtual addresses are activated.

```os
def init_paging():
    var i: usize = 0
    
    # 1. Clear the page directory (Set all entries to not present)
    while i < 1024:
        # Default PDE: Supervisor, Read/Write, Not Present (0x2)
        page_directory[i] = PAGE_RW
        i = i + 1
        
    # 2. Fill the first page table (Identity map 0x0 to 0x400000 - 4MB)
    i = 0
    while i < 1024:
        # Address is i * 4096. Flags are Present (0x1) | Read/Write (0x2)
        var physical_addr: u32 = (i * 4096) as u32
        first_page_table[i] = physical_addr | PAGE_PRESENT | PAGE_RW
        i = i + 1

    # 3. Put the first page table into the page directory
    @unsafe:
        var pt_ptr: usize = first_page_table as usize
        page_directory[0] = (pt_ptr as u32) | PAGE_PRESENT | PAGE_RW
```

---

## 3. Enabling Paging via CR3 and CR0

To turn paging on, we must load the physical address of our `page_directory` into CPU Control Register 3 (`cr3`), and then flip the Paging Enable bit (bit 31) in Control Register 0 (`cr0`). This must be done via inline assembly inside an `@unsafe` block.

```os
def enable_paging():
    @unsafe:
        # Get the physical address of our page directory
        var pd_addr: usize = page_directory as usize
        
        # Load the directory address into CR3
        asm("mov %0, %%cr3" : : "r"(pd_addr))
        
        # Read CR0, set the Paging bit (0x80000000), and write it back
        var cr0_val: u32
        asm("mov %%cr0, %0" : "=r"(cr0_val))
        cr0_val = cr0_val | 0x80000000
        asm("mov %0, %%cr0" : : "r"(cr0_val))

    # Print success using our VGA logic
    # (Assuming print() is implemented using VGABuffer)
    # print("Paging is now active!")
```

Call `init_paging()` then `enable_paging()` in your `kernel_main()`, and you have successfully activated virtual memory in OS-Lang!



---

## Chapter 5: The Kernel Heap & Custom Allocators

Now that our virtual memory engine maps raw 4KB pages of RAM, we face a practical limitation: our kernel cannot easily manage dynamic, variable-sized data structures at runtime. We need a system heap.

In this chapter, we will implement the native OS-Lang `Allocator` trait to build a deterministic **Kernel Bump Allocator**, bridging the gap between page-level allocation and byte-level memory management.

---

### 5.1 The Allocation Landscape: Pages vs. Heap

Paging manages memory at a macro level (4096-byte boundaries). The Heap manages memory at a micro level (allocating 16 bytes for a string, 64 bytes for a structural driver profile). 

Our heap allocator will claim a large region of pre-mapped virtual memory addresses (e.g., starting at `0x40000000`) and carve it up for the kernel whenever dynamic allocation requests occur.

---

### 5.2 Implementing the Core Allocator Trait

Section 10 of the OS-Lang Specification outlines the mandatory interface for dynamic memory. We must bind our custom implementation to the compiler's internal allocation hook.

Here is how we model a lightweight, deterministic Bump Allocator in native OS-Lang:

```os
# Chapter 5: The Heap Allocator

# Define structure tracking our sequential heap boundary limits
struct BumpAllocator:
    heap_start: usize
    heap_end: usize
    next_alloc: usize
    alloc_count: usize

# Global instance of our allocator state
var KERNEL_ALLOCATOR: BumpAllocator

def init_heap(start_address: usize, size_bytes: usize):
    KERNEL_ALLOCATOR.heap_start = start_address
    KERNEL_ALLOCATOR.heap_end = start_address + size_bytes
    KERNEL_ALLOCATOR.next_alloc = start_address
    KERNEL_ALLOCATOR.alloc_count = 0

# Implement the core language compiler allocation hook
@no_mangle
def os_alloc(size: usize, alignment: usize) -> ptr:
    @unsafe:
        # Align the next allocation address to match CPU boundary rules
        var current_ptr: usize = KERNEL_ALLOCATOR.next_alloc
        var alignment_mask: usize = alignment - 1
        
        # Fast bitwise alignment padding calculation
        if (current_ptr & alignment_mask) != 0:
            current_ptr = (current_ptr + alignment) & ~alignment_mask
            
        var next_ptr: usize = current_ptr + size
        
        # Trap an Out-of-Memory event via our panic handler if boundaries are breached
        if next_ptr > KERNEL_ALLOCATOR.heap_end:
            return 0 as ptr # Returning null forces a compiler-level allocation panic
            
        # Update allocator internal state tracker
        KERNEL_ALLOCATOR.next_alloc = next_ptr
        KERNEL_ALLOCATOR.alloc_count = KERNEL_ALLOCATOR.alloc_count + 1
        
        return current_ptr as ptr

@no_mangle
def os_free(target_ptr: ptr, size: usize, alignment: usize):
    # A true Bump Allocator cannot easily free memory individual blocks.
    # Memory is reclaimed globally by resetting the allocation count to zero.
    @unsafe:
        KERNEL_ALLOCATOR.alloc_count = KERNEL_ALLOCATOR.alloc_count - 1
        if KERNEL_ALLOCATOR.alloc_count == 0:
            KERNEL_ALLOCATOR.next_alloc = KERNEL_ALLOCATOR.heap_start

```

---

### 5.3 Activating Dynamic Allocations

With the `os_alloc` and `os_free` hooks bound, we can initialize our heap immediately after paging goes live in our bootstrap pipeline.

```os
@no_mangle
def kernel_init_sequence():
    # Step 1: Initialize Virtual Memory Paging Maps
    init_paging()
    
    # Step 2: Establish a 2MB Kernel Heap starting at virtual address 1GB mark
    var heap_base: usize = 0x40000000
    var heap_size: usize = 0x200000 # 2 Megabytes
    init_heap(heap_base, heap_size)
    
    # Verification: Explicitly allocate dynamic byte structures safely
    @unsafe:
        var dynamic_buffer: ptr = os_alloc(512, 8)
        if dynamic_buffer == (0 as ptr):
            # Panic if allocation engine fails
            on_panic("Heap Initialization Failed" as ptr, 42_u32, "OOM" as ptr)

```

---

### 5.4 Edge Cases & Hardware Warnings

> ### ⚠️ WARNING: Fragmentation and Lifespans
> 
> 
> Bump allocation is incredibly efficient ($O(1)$ execution time) and perfect for initializing permanent system tables. However, because `os_free` does not track individual holes in memory, using it for short-lived, repetitive allocations will cause the heap to run out of memory quickly. For complex user-space workloads later, we must upgrade this implementation to a Linked-List or Buddy Allocator model.



---

## Chapter 6: Multitasking & Context Switching

Up to this point, our kernel has executed code in a single, linear timeline. To build a modern operating system, we must allow multiple execution paths (tasks) to share the CPU concurrently.

In this chapter, we will implement **Cooperative Multitasking**. We will define a Process Control Block (PCB), dynamically allocate isolated execution stacks using our kernel heap, and write a low-level context switcher that swaps CPU register states mid-execution.

---

### 6.1 The Process Control Block (PCB)

To pause a running task and resume it later, we must save the exact state of the CPU registers at the moment execution is suspended. We store this metadata inside a custom structure called a Process Control Block.

Here is how we model a task structure in OS-Lang:

```os
# Chapter 6: Multitasking Management

@packed
struct ProcessControlBlock:
    id: i32
    state: i32         # 0 = Ready, 1 = Running, 2 = Suspended
    stack_pointer: usize # Holds the saved RSP value when the task is inactive
    stack_base: usize    # The starting address of this task's heap-allocated stack

```

---

### 6.2 Allocating Isolated Task Stacks

Every independent task requires its own execution stack to keep track of its local variables, function call frames, and interrupt states. We will utilize our Chapter 5 heap allocation hook to provision a 4KB stack space for each unique task.

```os
# Track active processes
var MAX_TASKS: usize = 2
var task_table: ProcessControlBlock[2]
var current_task_index: usize = 0

def create_task(task_id: i32, entry_point: ptr) -> ptr:
    # Allocate a 4KB stack from our Kernel Bump Allocator
    var stack_size: usize = 4096
    var raw_stack: ptr = os_alloc(stack_size, 16)
    
    # Calculate the top of the stack (x86_64 stacks grow downwards in memory)
    var stack_top: usize = (raw_stack as usize) + stack_size
    
    @unsafe:
        # We must manually inject a fake execution frame onto the new stack.
        # When our context switcher restores this task for the first time,
        # it will pop these values into registers, and the 'ret' instruction
        # will jump straight to the function entry point.
        
        # Step down the stack pointer to simulate pushed registers
        # We simulate pushing: RIP (entry_point), then standard registers
        var stack_ptr: ptr = (stack_top - 8) as ptr
        *stack_ptr = entry_point as usize # Fake return address (RIP)
        
        # Move down to leave blank spaces for R15-R8, RBP, RDI, RSI, RDX, RCX, RBX, RAX
        # 15 registers * 8 bytes = 120 bytes
        var saved_rsp: usize = stack_top - 128
        
        # Store metadata inside our task structure table
        task_table[task_id as usize].id = task_id
        task_table[task_id as usize].state = 0 # Ready State
        task_table[task_id as usize].stack_pointer = saved_rsp
        task_table[task_id as usize].stack_base = raw_stack as usize
        
    return raw_stack

```

---

### 6.3 The Naked Context Switcher

The core mechanism of multitasking is the context switch. This operation cannot use traditional function prologues because saving the stack frames of the context switcher itself would corrupt the target process's stack footprint.

We mark the routine as `@naked` and pass parameters directly using the System V AMD64 ABI registers (`%rdi` for argument 1, `%rsi` for argument 2).

```os
# Core Context Switching Function
# System V ABI: current_rsp_ptr is passed in RDI, next_rsp is passed in RSI
@naked
def os_switch_context(current_rsp_ptr: ptr, next_rsp: usize):
    @unsafe:
        asm:
            # 1. Save current task's execution state onto its own stack
            "pushq %rax"
            "pushq %rbx"
            "pushq %rcx"
            "pushq %rdx"
            "pushq %rsi"
            "pushq %rdi"
            "pushq %rbp"
            "pushq %r8"
            "pushq %r9"
            "pushq %r10"
            "pushq %r11"
            "pushq %r12"
            "pushq %r13"
            "pushq %r14"
            "pushq %r15"
            
            # 2. Save current RSP to the current task's PCB tracking field
            "movq %rsp, (%rdi)"
            
            # 3. Load the next task's saved RSP into the hardware CPU register
            "movq %rsi, %rsp"
            
            # 4. Pop the next task's saved execution state off its stack
            "popq %r15"
            "popq %r14"
            "popq %r13"
            "popq %r12"
            "popq %r11"
            "popq %r10"
            "popq %r9"
            "popq %r8"
            "popq %rbp"
            "popq %rdi"
            "popq %rsi"
            "popq %rdx"
            "popq %rcx"
            "popq %rbx"
            "popq %rax"
            
            # 5. Return execution cleanly into the next task's active code track
            "ret"

```

---

### 6.4 The Cooperative Scheduler Routine

To yield execution time back and forth, tasks voluntarily trigger the scheduler by calling `yield`. This handles the rotation logic through our active task listing matrix.

```os
@no_mangle
def yield():
    var old_index: usize = current_task_index
    var next_index: usize = (current_task_index + 1) % MAX_TASKS
    
    current_task_index = next_index
    
    # Mark old task as Ready, new task as Running
    task_table[old_index].state = 0
    task_table[next_index].state = 1
    
    var current_pcb_rsp_ptr: ptr = (@unsafe: &task_table[old_index].stack_pointer) as ptr
    var next_pcb_rsp: usize = task_table[next_index].stack_pointer
    
    # Hand off CPU execution registers directly to the naked assembly engine
    os_switch_context(current_pcb_rsp_ptr, next_pcb_rsp)

```

---

### 6.5 Hardware Warnings & Execution Safeguards

> ### ⚠️ WARNING: Stack Overflows and Trashing
> 
> 
> Because our kernel allocates a fixed 4KB boundary line per task space on our basic Bump Allocator heap, nesting deep recursive execution calls or placing immense array maps locally inside a task function will breach the stack allocation floor. This will silently overwrite the metadata fields of adjacent blocks, inducing unpredictable hardware faults. Always monitor local variables memory costs within multi-threaded scopes.




---

## Chapter 7: PCI Bus Discovery & Hardware Scanning

Now that our kernel has a functioning scheduler, it must discover the physical peripheral hardware attached to the system motherboard rather than hardcoding memory addresses.

### 7.1 The PCI Configuration Space Mechanics

The x86 architecture uses Configuration Mechanism #1 to communicate with the PCI bus via I/O ports. We use `0xCF8` as the Address Port and `0xCFC` as the Data Port.

### 7.2 Modeling the PCI Configuration Payload

```os
@packed
struct PCIHeader:
    vendor_id: u16
    device_id: u16
    command: u16
    status: u16
    revision_id: u8
    prog_if: u8
    subclass: u8
    class_code: u8
    cache_line_size: u8
    latency_timer: u8
    header_type: u8
    bist: u8
```

### 7.3 Implementing the Bus Scan Algorithm

```os
def pci_config_read_word(bus: u8, slot: u8, func: u8, offset: u8) -> u16:
    var address: u32
    var lbus: u32 = bus as u32
    var lslot: u32 = slot as u32
    var lfunc: u32 = func as u32
    
    # Calculate address mapping
    address = (lbus << 16) | (lslot << 11) | (lfunc << 8) | (offset & 0xFC) as u32 | 0x80000000
    
    outb_32(0xCF8, address)
    var result: u32 = inb_32(0xCFC)
    return ((result >> ((offset & 2) * 8)) & 0xFFFF) as u16

def scan_pci_bus():
    var bus: u16 = 0
    var slot: u16 = 0
    while bus < 256:
        slot = 0
        while slot < 32:
            var vendor: u16 = pci_config_read_word(bus as u8, slot as u8, 0, 0)
            if vendor != 0xFFFF:
                # Device found, logic to read remaining headers goes here
                pass
            slot = slot + 1
        bus = bus + 1
```

### 7.4 Hardware Warning Callout
> ### ⚠️ WARNING: PCI Read Faults
> A Vendor ID of `0xFFFF` means no device is present on that slot. If you attempt to write to non-existent PCI addresses or unaligned memory offsets within the PCI space, it will immediately lock the CPU and trigger a bus fault!

---

## Chapter 8: Hard Drive Drivers & Raw Sector Storage (ATA/IDE PIO Mode)

### 8.1 PIO Mode Register Interfaces

The Primary ATA bus is mapped from port `0x1F0` to `0x1F7`. We send Logical Block Addressing (LBA) sector selections and sector counts to read and write bytes.

### 8.2 Reading Raw Sectors (LBA28)

```os
def ata_pio_read_sector(lba: u32, target_buffer: ptr):
    # Wait for drive to be ready (bit 7 clear)
    # ...
    
    # Send LBA addressing via outb
    outb(0x1F2, 1) # Read 1 sector
    outb(0x1F3, (lba & 0xFF) as u8)
    outb(0x1F4, ((lba >> 8) & 0xFF) as u8)
    outb(0x1F5, ((lba >> 16) & 0xFF) as u8)
    outb(0x1F6, (((lba >> 24) & 0x0F) | 0xE0) as u8)
    
    # Send Read Command
    outb(0x1F7, 0x20)
    
    # Poll for status (Wait for 0x08 DRQ bit)
    while (inb(0x1F7) & 0x08) == 0:
        pass
        
    # Read 256 16-bit words (512 bytes total)
    var i: usize = 0
    var buf_u16: ptr = target_buffer
    while i < 256:
        var word_data: u16 = inb_16(0x1F0)
        # write to buffer logic...
        i = i + 1
```

### 8.3 Writing Sectors to Disk

Writing works identically using command `0x30` on port `0x1F7`, followed by streaming 256 `u16` words out to the `0x1F0` port.

### 8.4 Hardware Warning Callout
> ### ⚠️ WARNING: PIO Bottlenecks
> ATA PIO Mode uses synchronous CPU polling loops, meaning the entire kernel freezes while waiting for disk operations. This is a massive bottleneck. Production kernels must eventually upgrade to DMA (Direct Memory Access).

---

## Chapter 9: The Virtual File System (VFS) & FAT File Engine

### 9.1 The FAT Boot Record Layout

```os
@packed
struct FAT16BPB:
    jmp: u8[3]
    oem_name: u8[8]
    bytes_per_sector: u16
    sectors_per_cluster: u8
    reserved_sectors: u16
    fat_count: u8
    root_dir_entries: u16
```

### 9.2 Navigating the Cluster Chain

Once we read the BPB, we can loop over root directory entries, check file name matching (8.3 layout), and extract the starting cluster index to parse the FAT table chain.

### 9.3 The VFS Layer Implementations

To standardize files, we map `open`, `read`, and `write` system calls using function pointers defined in OS-Lang over dynamically allocated `os_alloc` file descriptors.

### 9.4 Software Warning Callout
> ### ⚠️ WARNING: Memory Leakage
> Traversal of FAT directories requires loading multiple cluster chunks into RAM. If recursive directory tracking fails to `os_free` old sector buffers, the VFS will leak memory catastrophically and panic the system.

---

## Chapter 10: User Space Isolation (Ring 3) & System Calls

### 10.1 Expanding the GDT for User Space

We establish new GDT entries for User Code (Index 3) and User Data (Index 4), setting their Descriptor Privilege Level (DPL) to Ring 3.

### 10.2 The Ring 0 to Ring 3 Leap (`iretq` Context Jump)

```os
@naked
def jump_to_user_space(entry_point: usize, user_stack: usize):
    @unsafe:
        asm:
            "cli"
            # Push Ring 3 Stack Segment (User Data Selector = 0x20 | 3)
            "pushq $0x23"
            # Push Ring 3 Stack Pointer
            "pushq %rsi"
            # Push RFLAGS (Enable Interrupts = 0x200)
            "pushq $0x202"
            # Push Ring 3 Code Segment (User Code Selector = 0x18 | 3)
            "pushq $0x1B"
            # Push Instruction Pointer
            "pushq %rdi"
            # Execute hardware privilege drop
            "iretq"
```

### 10.3 Establishing the `syscall` Interceptor

Load the `IA32_LSTAR` MSR with your unified system call handler address so when User Space fires the `syscall` instruction, the CPU instantly snaps to Ring 0 execution.

### 10.4 Hardware Warning Callout
> ### ⚠️ WARNING: Kernel Panic on User Stack
> Upon entering a syscall, the CPU must immediately use `swapgs` to switch internal tracking pointers. Operating on the untrusted User Stack inside Ring 0 is a massive security and stability flaw!

---

## Chapter 11: The Kernel Command-Line Interface Shell

### 11.1 Processing Streaming String Input Line Buffers

Buffer keyboard IRQ 1 characters in a dynamic `os_alloc` byte array until `\n` is read.

### 11.2 String Comparison & Tokenization Engines

Manually implement non-hosted string matching (`strcmp`, `strtok`) using raw pointer arithmetic in OS-Lang to parse the buffer into an executable command.

### 11.3 Launching Dynamic Programs

Resolve the tokenized command through the VFS (Chapter 9), parse the ELF binary, allocate new execution stacks (Chapter 6), and perform a Ring 3 leap (Chapter 10).

---

## Chapter 12: Multicore Processing (SMP) & Final ISO Automation

### 12.1 Initializing the Local APIC

Read the ACPI tables to find the base physical address of the Local APIC, configure its timer, and map its spurious interrupt vector.

### 12.2 The Multicore Boot Sequence (Trampoline Code)

To wake secondary Application Processors (APs), send an `INIT` Inter-Processor Interrupt (IPI) followed by a `STARTUP` IPI (SIPI) pointing to a physical 16-bit trampoline boot sequence. 

### 12.3 Automated Live ISO Distro Generation

```bash
mkdir -p isodir/boot/grub
cp my_kernel.bin isodir/boot/my_kernel.bin
echo 'menuentry "OS-Lang" { multiboot /boot/my_kernel.bin }' > isodir/boot/grub/grub.cfg
grub-mkrescue -o os-lang-live.iso isodir
```

With this, your complete OS-Lang bare-metal ecosystem is built, compiled, scheduled, isolated, and bundled into a deployable ISO image!
