# Environment Setup (QEMU)

To run the operating system you write in OS-Lang, you will need a virtual machine emulator like **QEMU**.

## Installing QEMU

**Windows:**
Download the binaries from the official [QEMU website](https://www.qemu.org/download/).

**macOS:**
```bash
brew install qemu
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install qemu-system-x86
```

## Compiling Your First Kernel

OS-Lang compiles to an object file (`.o`), which you then link using standard GNU tools or `lld`.

```bash
# 1. Compile OS-Lang to LLVM IR and then to an object file
python build_kernel.py

# 2. Run in QEMU
qemu-system-x86_64 -kernel kernel.bin
```
