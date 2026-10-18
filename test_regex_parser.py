from regex_parser import RegexParser

tests = [
    "a",
    "abc",
    "a|b",
    "a*",
    "b+",
    "a?",
    "[0-9]+",
    "[A-Za-z_][A-Za-z0-9_]*",
    r"\+",
]
def print_tree(node, indent=""):
    if node is None:
        return

    print(indent + node.node_type, end="")

    if node.value is not None:
        print(f": {node.value}")
    else:
        print()

    if node.left is not None:
        print(indent + "  LEFT:")
        print_tree(node.left, indent + "    ")

    if node.right is not None:
        print(indent + "  RIGHT:")
        print_tree(node.right, indent + "    ")

for regex in tests:
    print(f"\nRegex: {regex}")
    try:
        parser = RegexParser(regex)
        tree = parser.parse()
        print_tree(tree)
    except ValueError as e:
        print("Error:", e)

