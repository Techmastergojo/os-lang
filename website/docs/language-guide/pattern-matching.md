# Pattern Matching (`match`)

Instead of managing floating integer constants, OS-Lang provides zero-cost `enum` types and the `match` statement. `match` is compiled down directly to highly optimized LLVM `switch` tables, ensuring `O(1)` branching performance.

```os-lang
enum ThreadState {
    RUNNING,
    BLOCKED,
    SLEEPING
}

fn process_thread(state: ThreadState) -> void:
    match state:
        ThreadState.RUNNING =>:
            print("Executing...")
        ThreadState.BLOCKED =>:
            print("Waiting for I/O")
        _ =>:
            print("Default catch-all for sleeping")
```
