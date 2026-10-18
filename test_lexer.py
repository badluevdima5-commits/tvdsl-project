import unittest
from lexer import build_lexer


class TestLexer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lexer, _, _ = build_lexer()

    def tokenize(self, input_string):
        tokens = self.lexer.tokenize(input_string)
        return [token['type'] for token in tokens]

    def test_empty_string(self):
        tokens = self.tokenize("")
        self.assertEqual(tokens, [])

    def test_whitespace_only(self):
        tokens = self.tokenize("   ")
        self.assertEqual(tokens, [])

        tokens = self.tokenize("\t\t\t")
        self.assertEqual(tokens, [])

        tokens = self.tokenize("  \t  \n  \r\n  ")
        self.assertEqual(tokens, [])

    def test_integers(self):
        tokens = self.tokenize("0")
        self.assertEqual(tokens, ["INT"])

        tokens = self.tokenize("123")
        self.assertEqual(tokens, ["INT"])

        tokens = self.tokenize("00")
        self.assertEqual(tokens, ["INT"])

        tokens = self.tokenize("01")
        self.assertEqual(tokens, ["INT"])

    def test_identifiers(self):
        tokens = self.tokenize("x")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("_var")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("my_variable")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("var123")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("_123")
        self.assertEqual(tokens, ["IDENT"])

    def test_keywords(self):
        keywords = [
            "function", "returns", "requires", "ensures", "uses",
            "if", "else", "while", "invariant",
            "assert", "assume",
            "forall", "exists",
            "true", "false",
            "and", "or", "not",
            "length"
        ]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                tokens = self.tokenize(keyword)
                self.assertEqual(len(tokens), 1)
                self.assertEqual(tokens[0], keyword.upper())

    def test_keyword_vs_identifier(self):
        tokens = self.tokenize("ifx")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("while1")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("_function")
        self.assertEqual(tokens, ["IDENT"])

    def test_operators(self):
        test_cases = [
            ("+", ["PLUS"]),
            ("-", ["MINUS"]),
            ("*", ["TIMES"]),
            ("/", ["DIVIDE"]),
            ("=", ["ASSIGN"]),
            ("==", ["EQ"]),
            ("!=", ["NEQ"]),
            ("<", ["LT"]),
            ("<=", ["LEQ"]),
            (">", ["GT"]),
            (">=", ["GEQ"]),
            ("->", ["ARROW"]),
        ]

        for input_str, expected in test_cases:
            with self.subTest(operator=input_str):
                tokens = self.tokenize(input_str)
                self.assertEqual(tokens, expected)

    def test_delimiters(self):
        test_cases = [
            ("(", ["LPAREN"]),
            (")", ["RPAREN"]),
            ("{", ["LBRACE"]),
            ("}", ["RBRACE"]),
            ("[", ["LBRACKET"]),
            ("]", ["RBRACKET"]),
            (";", ["SEMICOLON"]),
            (",", ["COMMA"]),
            (":", ["COLON"]),
            ("|", ["PIPE"]),
        ]

        for input_str, expected in test_cases:
            with self.subTest(delimiter=input_str):
                tokens = self.tokenize(input_str)
                self.assertEqual(tokens, expected)

    def test_comments(self):
        tokens = self.tokenize("// this is a comment")
        self.assertEqual(tokens, [])

        tokens = self.tokenize("x // comment")
        self.assertEqual(tokens, ["IDENT"])

        tokens = self.tokenize("42 // number\ny")
        self.assertEqual(tokens, ["INT", "IDENT"])

    def test_function_declaration(self):
        input_str = "function add(x: int, y: int) returns sum: int"
        tokens = self.tokenize(input_str)
        expected = [
            "FUNCTION", "IDENT", "LPAREN", "IDENT", "COLON", "IDENT",
            "COMMA", "IDENT", "COLON", "IDENT", "RPAREN",
            "RETURNS", "IDENT", "COLON", "IDENT"
        ]
        self.assertEqual(tokens, expected)

    def test_expression(self):
        input_str = "x + y * 2 - 1"
        tokens = self.tokenize(input_str)
        expected = ["IDENT", "PLUS", "IDENT", "TIMES", "INT", "MINUS", "INT"]
        self.assertEqual(tokens, expected)

    def test_array_access(self):
        input_str = "arr[i]"
        tokens = self.tokenize(input_str)
        expected = ["IDENT", "LBRACKET", "IDENT", "RBRACKET"]
        self.assertEqual(tokens, expected)

    def test_comparison_operators(self):
        input_str = "x == y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "EQ", "IDENT"])

        input_str = "x != y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "NEQ", "IDENT"])

        input_str = "x <= y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "LEQ", "IDENT"])

        input_str = "x >= y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "GEQ", "IDENT"])

    def test_logical_operators(self):
        input_str = "true and false"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["TRUE", "AND", "FALSE"])

        input_str = "x or not y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "OR", "NOT", "IDENT"])

    def test_implication(self):
        input_str = "x -> y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "ARROW", "IDENT"])

    def test_quantifiers(self):
        input_str = "forall(i: int | i >= 0)"
        tokens = self.tokenize(input_str)
        expected = [
            "FORALL", "LPAREN", "IDENT", "COLON", "IDENT", "PIPE",
            "IDENT", "GEQ", "INT", "RPAREN"
        ]
        self.assertEqual(tokens, expected)

        input_str = "exists(x: int | x > 0)"
        tokens = self.tokenize(input_str)
        expected = [
            "EXISTS", "LPAREN", "IDENT", "COLON", "IDENT", "PIPE",
            "IDENT", "GT", "INT", "RPAREN"
        ]
        self.assertEqual(tokens, expected)

    def test_complete_function(self):
        input_str = """
        function factorial(n: int)
        requires n >= 0
        returns result: int
        uses i
        {
            result = 1;
            i = 1;
            while (i <= n)
            invariant result >= 1
            {
                result = result * i;
                i = i + 1;
            }
        }
        """
        tokens = self.tokenize(input_str)
                                                     
        self.assertGreater(len(tokens), 0)
        self.assertEqual(tokens[0], "FUNCTION")

    def test_assert_assume(self):
        input_str = "assert x > 0;"
        tokens = self.tokenize(input_str)
        expected = ["ASSERT", "IDENT", "GT", "INT", "SEMICOLON"]
        self.assertEqual(tokens, expected)

        input_str = "assume x != 0;"
        tokens = self.tokenize(input_str)
        expected = ["ASSUME", "IDENT", "NEQ", "INT", "SEMICOLON"]
        self.assertEqual(tokens, expected)

    def test_invalid_character(self):
        with self.assertRaises(ValueError) as context:
            self.tokenize("x $ y")
        self.assertIn("Unexpected character", str(context.exception))

    def test_non_ascii(self):
        with self.assertRaises(ValueError):
            self.tokenize("привет")

        with self.assertRaises(ValueError):
            self.tokenize("x + ы")

    def test_division_vs_comment(self):
        input_str = "x / y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT", "DIVIDE", "IDENT"])

                             
        input_str = "x // y"
        tokens = self.tokenize(input_str)
        self.assertEqual(tokens, ["IDENT"])

    def test_operator_precedence_example(self):
        input_str = "a = b + c * d / e - f"
        tokens = self.tokenize(input_str)
        expected = [
            "IDENT", "ASSIGN", "IDENT", "PLUS", "IDENT", "TIMES",
            "IDENT", "DIVIDE", "IDENT", "MINUS", "IDENT"
        ]
        self.assertEqual(tokens, expected)

    def test_negative_numbers(self):
        input_str = "-42"
        tokens = self.tokenize(input_str)
                                                   
        self.assertEqual(tokens, ["MINUS", "INT"])


if __name__ == "__main__":
    unittest.main()
