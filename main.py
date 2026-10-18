import sys
import json
from lexer import build_lexer
from parser import parse, ParseError
from ast_printer import print_ast, ast_to_json


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <input_file.funny> [--json]")
        print("       python3 main.py --stdin [--json]")
        sys.exit(1)

    # Build lexer
    print("Building lexer...", file=sys.stderr)
    lexer, dfa_size, minimized_size = build_lexer()
    print(f"  DFA: {dfa_size} states → {minimized_size} states after minimization\n", file=sys.stderr)

    # Read input
    if sys.argv[1] == '--stdin':
        input_text = sys.stdin.read()
        output_json = '--json' in sys.argv[2:]
    else:
        input_file = sys.argv[1]
        output_json = '--json' in sys.argv[2:]

        try:
            with open(input_file, 'r') as f:
                input_text = f.read()
        except FileNotFoundError:
            print(f"Error: File '{input_file}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Tokenize
    try:
        print("Tokenizing...", file=sys.stderr)
        tokens = lexer.tokenize(input_text)
        print(f"  Generated {len(tokens)} tokens\n", file=sys.stderr)
    except ValueError as e:
        print(f"Lexical error: {e}", file=sys.stderr)
        sys.exit(1)

    # Parse
    try:
        print("Parsing...", file=sys.stderr)
        ast = parse(tokens)
        print(f"  Successfully parsed module with {len(ast.functions)} functions and {len(ast.formulas)} formulas\n",
              file=sys.stderr)
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output AST
    if output_json:
        print(ast_to_json(ast))
    else:
        print(print_ast(ast))


if __name__ == "__main__":
    main()
