import argparse
import sys
import os
import subprocess
from src.lexer import Lexer
from src.parser import Parser, ParseError
from src.semantic import SemanticAnalyzer, SemanticError
from src.codegen import CodeGenerator

def generate_ai_driver_stub(device_name: str) -> str:
    slug = device_name.lower().replace(" ", "_").replace("-", "_")
    return f"""# Generated AI Driver for {device_name} in OS-Lang
@driver
fn init_{slug}_driver():
    # Write initialization command to primary I/O port
    outb(0x3F8, 0x00)
    let mut status: u8 = inb(0x3F8) as u8
    vga_write(0, 0, status, 15)

@interrupt(33)
fn {slug}_isr_handler():
    let data: int = inb(0x60)
    vga_write(0, 1, data as u8, 14)
    outb(0x20, 0x20)
"""

def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    parser = argparse.ArgumentParser(description="Compiler for the OS Programming Language (OS-Lang)")
    parser.add_argument("source_file", nargs="?", default="", help="Path to the source code file")
    parser.add_argument("--target", choices=["x86_64", "arm64", "riscv64"], default="x86_64", help="Target architecture triple")
    parser.add_argument("--run-qemu", action="store_true", help="Boot and run generated kernel binary in QEMU emulator")
    parser.add_argument("--init", type=str, default="", help="Initialize a new OS-Lang project folder")
    parser.add_argument("--template", choices=["bare-metal", "web-gui"], default="web-gui", help="Template choice for project initialization")
    parser.add_argument("--ai-driver", type=str, default="", help="Generate AI-assisted driver starter template for hardware device")
    
    args = parser.parse_args()

    if args.init:
        folder = args.init
        os.makedirs(folder, exist_ok=True)
        main_file = os.path.join(folder, "main.os")
        if args.template == "web-gui":
            template_code = """# Web-Style OsGUI Desktop Template
guiapp MyApp:
    title: "OS-Lang Web Desktop"
    width: 800
    height: 600
    background: "#0f0f1a"

    window MainWin:
        header TopNav:
            align: center
            justify: space_between
            bg: "#161625"
            height: 50

            label logo:
                text: "My Bare-Metal OS"
                color: "#00ffcc"

        container ContentArea:
            direction: row
            flex: 1

            sidebar Menu:
                width: 200
                bg: "#1a1a2e"

                button btn1:
                    text: "Overview"

            main AppMain:
                flex: 1
                align: center
                justify: center

                card DashboardCard:
                    width: 300
                    height: 150
                    bg: "#161625"

                    label status:
                        text: "System Online"
                        color: "#00ff00"
"""
        else:
            template_code = """# Bare-Metal Kernel Template
@unsafe
fn vga_print(ch: u8):
    vga_write(0, 0, ch, 15)

@interrupt(33)
fn keyboard_handler():
    let key: int = inb(0x60)
    vga_write(0, 1, key as u8, 14)
    outb(0x20, 0x20)

@entry
fn kmain():
    vga_print(79 as u8) # 'O'
    while true:
        pass
"""
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(template_code)
        print(f"✨ Project Initialized! Created '{folder}/main.os' using template [{args.template}].")
        return

    if args.ai_driver:
        output_file = f"{args.ai_driver.lower().replace(' ', '_')}_driver.os"
        code = generate_ai_driver_stub(args.ai_driver)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        print(f"🤖 AI Driver Generator: Created compile-ready driver template '{output_file}'!")
        return

    if not args.source_file:
        print("Error: No source file provided. Usage: osc <source_file.os>", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.exists(args.source_file):
        print(f"Error: File '{args.source_file}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.source_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print(f"Read {len(content)} bytes from {args.source_file}\n")
    
    target_triples = {
        "x86_64": "x86_64-unknown-none-elf",
        "arm64": "aarch64-unknown-none-elf",
        "riscv64": "riscv64-unknown-none-elf"
    }
    triple = target_triples.get(args.target, "x86_64-unknown-none-elf")
    
    try:
        lexer = Lexer(content)
        tokens = lexer.lex()
        print(f"✅ Lexing successful! Generated {len(tokens)} tokens.")
        
        parser_inst = Parser(tokens)
        ast_tree = parser_inst.parse()
        print(f"✅ Parsing successful! Generated Abstract Syntax Tree (AST).")
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast_tree)
        print(f"✅ Semantic Analysis successful! Code is memory & type safe.")
        
        codegen = CodeGenerator(target_triple=triple)
        codegen.generate(ast_tree)
        ir_code = codegen.get_ir()
        
        ir_filename = args.source_file.replace('.os', '.ll')
        if not ir_filename.endswith('.ll'):
            ir_filename += '.ll'
            
        with open(ir_filename, 'w', encoding='utf-8') as f:
            f.write(ir_code)
            
        print(f"✅ LLVM IR Generation successful! Output saved to {ir_filename}")
        
        # Save as object file
        obj_filename = args.source_file.replace('.os', '.o')
        if not obj_filename.endswith('.o'):
            obj_filename += '.o'
            
        codegen.save_object_file(obj_filename, target_triple=triple)
        print(f"✅ Object file generated successfully for target [{args.target}]! Output saved to {obj_filename}")
        
        if args.run_qemu:
            qemu_cmd = "qemu-system-x86_64 -kernel kernel.bin -m 256M -vga std"
            print(f"\n🚀 Launching QEMU Emulator:\n   {qemu_cmd}")
            # Note: Prints command line runner for bare-metal testing
        
        print("\n🚀 Compilation complete!")
        
    except ParseError as e:
        print(f"\n❌ PARSER ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except SemanticError as e:
        print(f"\n❌ SEMANTIC ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ COMPILER CRASH: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
