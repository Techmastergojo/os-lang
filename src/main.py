import argparse
import sys
import os
from src.lexer import Lexer
from src.parser import Parser, ParseError
from src.semantic import SemanticAnalyzer, SemanticError
from src.codegen import CodeGenerator
def main():
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
            
    parser = argparse.ArgumentParser(description="Compiler for the OS Programming Language")
    parser.add_argument("source_file", help="Path to the source code file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.source_file):
        print(f"Error: File '{args.source_file}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.source_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print(f"Read {len(content)} bytes from {args.source_file}\n")
    
    try:
        lexer = Lexer(content)
        tokens = lexer.lex()
        print(f"✅ Lexing successful! Generated {len(tokens)} tokens.")
        
        parser = Parser(tokens)
        ast_tree = parser.parse()
        print(f"✅ Parsing successful! Generated Abstract Syntax Tree (AST).")
        
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast_tree)
        print(f"✅ Semantic Analysis successful! Code is memory & type safe.")
        
        codegen = CodeGenerator()
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
            
        codegen.save_object_file(obj_filename)
        print(f"✅ Object file generated successfully! Output saved to {obj_filename}")
        
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
