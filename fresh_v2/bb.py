import sys
from pathlib import Path
from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.semantic import analyze
from compiler.ir import generate
from compiler.bytecode import compile_ir
from runtime.vm import VirtualMachine

def compile_source(source):
    ast = parse(tokenize(source))
    analyze(ast)
    return compile_ir(generate(ast))

def run_source(source, input_fn=None):
    return VirtualMachine(input_fn=input_fn).run(compile_source(source))

def main():
    if len(sys.argv) != 2:
        print("Usage: python bb.py FILE.bb")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    for result in run_source(path.read_text(encoding="utf-8")):
        print(result)

if __name__ == "__main__":
    main()
