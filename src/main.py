import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Compiler for the OS Programming Language")
    parser.add_argument("source_file", help="Path to the source code file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.source_file):
        print(f"Error: File '{args.source_file}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.source_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print(f"Read {len(content)} bytes from {args.source_file}")

if __name__ == "__main__":
    main()
