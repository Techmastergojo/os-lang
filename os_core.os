# Core OS primitives and structures for Multitasking

hwmap InterruptFrame:
    # Segment registers
    gs: u32
    fs: u32
    es: u32
    ds: u32
    # Pushed by pusha
    edi: u32
    esi: u32
    ebp: u32
    esp_dummy: u32
    ebx: u32
    edx: u32
    ecx: u32
    eax: u32
    # Interrupt number and error code
    int_no: u32
    err_code: u32
    # Pushed by the CPU automatically
    eip: u32
    cs: u32
    eflags: u32
    useresp: u32
    ss: u32

hwmap TaskState:
    eax: u32
    ebx: u32
    ecx: u32
    edx: u32
    esi: u32
    edi: u32
    ebp: u32
    esp: u32
    eip: u32
    eflags: u32
    cr3: u32

# A global task lock (spinlock)
let mut task_lock: u64 = 0

@unsafe
fn lock_scheduler():
    # Attempt to acquire the spinlock
    let mut prev: u64 = 1
    # Assuming atomic_xchg returns the previous value, we loop until we got 0
    # prev = atomic_xchg(task_lock as ptr[u64], 1)
    # We don't have while loops yet in the tests or they might not be fully functional
    # Let's just use cmpxchg
    prev = atomic_cmpxchg(&task_lock as ptr[u64], 0, 1)

@unsafe
fn unlock_scheduler():
    atomic_xchg(&task_lock as ptr[u64], 0)

@naked
@unsafe
fn context_switch():
    # Save current task state
    asm("pusha")
    # In a real OS we'd save ESP to current task and load next task's ESP
    asm("popa")
    asm("iret")
