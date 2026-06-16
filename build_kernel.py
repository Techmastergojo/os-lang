import os
import subprocess
import sys

def build():
    # 1. Compile the kernel source to object file
    print("Compiling kernel.os...")
    result = subprocess.run([sys.executable, "-m", "src.main", "kernel.os"])
    if result.returncode != 0:
        print("Failed to compile kernel.os")
        sys.exit(1)
        
    # 2. Check if ld.lld or ld is available
    linker = None
    for l in ['ld.lld', 'ld']:
        try:
            subprocess.run([l, "--version"], capture_output=True)
            linker = l
            break
        except FileNotFoundError:
            continue
            
    if not linker:
        print("\n[WARNING] Linker (ld.lld or ld) not found on PATH.")
        print("To complete bare-metal linking, install LLVM (lld) or a cross-compiler like x86_64-elf-gcc.")
        print("However, the object file 'kernel.o' was successfully generated!")
        return

    # 3. Link the object file into a binary
    print(f"\nLinking with {linker}...")
    link_cmd = [
        linker,
        "-T", "linker.ld",
        "-o", "kernel.bin",
        "kernel.o"
    ]
    
    link_result = subprocess.run(link_cmd)
    if link_result.returncode == 0:
        print("✅ Kernel binary 'kernel.bin' linked successfully!")
        
if __name__ == "__main__":
    build()
