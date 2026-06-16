import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

class OSCompilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Next-Gen OS Compiler")
        self.root.geometry("600x500")
        self.root.configure(bg="#1e1e1e")
        
        # Header
        header = tk.Label(root, text="OS Language Compiler", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="#00A859")
        header.pack(pady=10)
        
        # File Selection
        frame = tk.Frame(root, bg="#1e1e1e")
        frame.pack(pady=10)
        
        self.file_path_var = tk.StringVar()
        self.file_entry = tk.Entry(frame, textvariable=self.file_path_var, width=50, font=("Segoe UI", 10))
        self.file_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = tk.Button(frame, text="Browse .os File", command=self.browse_file, bg="#333333", fg="white", font=("Segoe UI", 10))
        browse_btn.pack(side=tk.LEFT)
        
        # Compile Button
        compile_btn = tk.Button(root, text="🚀 Compile & Build", command=self.compile_code, bg="#007acc", fg="white", font=("Segoe UI", 12, "bold"), width=20)
        compile_btn.pack(pady=15)
        
        # Output Console
        tk.Label(root, text="Compiler Output:", bg="#1e1e1e", fg="white", font=("Segoe UI", 10)).pack(anchor="w", padx=20)
        self.console = scrolledtext.ScrolledText(root, width=70, height=15, bg="#000000", fg="#00FF00", font=("Consolas", 10))
        self.console.pack(padx=20, pady=5)
        
    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.root.update()

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("OS Language Files", "*.os"), ("All Files", "*.*")])
        if file_path:
            self.file_path_var.set(file_path)

    def compile_code(self):
        source_file = self.file_path_var.get()
        if not source_file or not os.path.exists(source_file):
            messagebox.showerror("Error", "Please select a valid .os file first!")
            return
            
        self.console.delete(1.0, tk.END)
        self.log(f"Compiling: {os.path.basename(source_file)}...")
        
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.log(f"Read {len(content)} bytes.")
            
            # 1. Lexer
            lexer = Lexer(content)
            tokens = lexer.lex()
            self.log(f"✅ Lexing successful! ({len(tokens)} tokens)")
            
            # 2. Parser
            parser = Parser(tokens)
            ast_tree = parser.parse()
            self.log("✅ Parsing successful! AST generated.")
            
            # 3. Semantic Analysis
            analyzer = SemanticAnalyzer()
            analyzer.analyze(ast_tree)
            self.log("✅ Semantic Analysis successful! Code is safe.")
            
            # 4. Code Generation
            codegen = CodeGenerator()
            codegen.generate(ast_tree)
            ir_code = codegen.get_ir()
            
            # Save files
            base_name = source_file.replace('.os', '')
            ir_filename = base_name + '.ll'
            obj_filename = base_name + '.o'
            
            with open(ir_filename, 'w', encoding='utf-8') as f:
                f.write(ir_code)
            self.log(f"✅ LLVM IR saved to: {os.path.basename(ir_filename)}")
            
            codegen.save_object_file(obj_filename)
            self.log(f"✅ Object file saved to: {os.path.basename(obj_filename)}")
            
            self.log("\n🚀 Compilation Complete! Ready to boot.")
            messagebox.showinfo("Success", "Compilation completed successfully! Your machine code (.o) is ready.")
            
        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}")
            messagebox.showerror("Compiler Error", str(e))

def main_gui():
    root = tk.Tk()
    app = OSCompilerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui()
