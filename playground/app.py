import os
import sys
from flask import Flask, request, jsonify, render_template_string

# Add project root to sys.path to import compiler modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.codegen import CodeGenerator

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Next-Gen OS Language Playground</title>
    <style>
        body { font-family: 'Inter', sans-serif; margin: 0; padding: 20px; background-color: #121212; color: #ffffff; }
        .container { display: flex; flex-direction: column; height: 90vh; }
        .header { margin-bottom: 20px; }
        .main { display: flex; flex: 1; gap: 20px; }
        .editor-container, .output-container { flex: 1; display: flex; flex-direction: column; }
        textarea { width: 100%; flex: 1; font-family: monospace; font-size: 14px; background: #1e1e1e; color: #d4d4d4; border: 1px solid #333; padding: 10px; resize: none; border-radius: 4px; }
        pre { width: 100%; flex: 1; background: #1e1e1e; color: #569cd6; border: 1px solid #333; padding: 10px; overflow: auto; border-radius: 4px; margin: 0; }
        button { background-color: #007acc; color: white; border: none; padding: 10px 20px; font-size: 16px; cursor: pointer; border-radius: 4px; align-self: flex-start; margin-top: 10px; }
        button:hover { background-color: #005999; }
        .error { color: #f44747; }
        h2 { font-size: 18px; margin-top: 0; color: #cccccc; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>OS Language Playground</h1>
            <p>Write your OS code below and compile it to LLVM IR instantly in the browser.</p>
        </div>
        <div class="main">
            <div class="editor-container">
                <h2>Source Code (.os)</h2>
                <textarea id="source-code">
@unsafe
fn print_char(port: u16, val: u8):
    outb(port, val)

fn main() -> int:
    let x: int = 42
    return x
</textarea>
                <button onclick="compileCode()">Compile to LLVM IR</button>
            </div>
            <div class="output-container">
                <h2>Compiler Output</h2>
                <pre id="output">Output will appear here...</pre>
            </div>
        </div>
    </div>

    <script>
        async function compileCode() {
            const source = document.getElementById('source-code').value;
            const outputElement = document.getElementById('output');
            outputElement.textContent = 'Compiling...';
            outputElement.className = '';

            try {
                const response = await fetch('/compile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source })
                });
                
                const data = await response.json();
                if (response.ok) {
                    outputElement.textContent = data.ir;
                } else {
                    outputElement.textContent = 'Error: ' + data.error;
                    outputElement.className = 'error';
                }
            } catch (err) {
                outputElement.textContent = 'Request failed: ' + err.message;
                outputElement.className = 'error';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    if not data or 'source' not in data:
        return jsonify({'error': 'No source code provided'}), 400
    
    source = data['source']
    try:
        lexer = Lexer(source)
        tokens = lexer.lex()
        
        parser = Parser(tokens)
        ast_root = parser.parse()
        
        semantic = SemanticAnalyzer()
        semantic.analyze(ast_root)
        
        codegen = CodeGenerator()
        codegen.generate(ast_root)
        
        return jsonify({'ir': str(codegen.module)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
