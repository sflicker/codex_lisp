import unittest

from interpreter import LispSyntaxError, parse, parse_program, tokenize


class ParserTests(unittest.TestCase):
    def test_tokenize_nested_expression(self):
        self.assertEqual(
            tokenize("(+ 1 (* 2 3))"),
            ["(", "+", "1", "(", "*", "2", "3", ")", ")"],
        )

    def test_parse_nested_expression(self):
        self.assertEqual(parse("(+ 1 (* 2 3))"), ["+", 1, ["*", 2, 3]])

    def test_parse_numbers_and_symbols(self):
        self.assertEqual(parse("42"), 42)
        self.assertEqual(parse("3.5"), 3.5)
        self.assertEqual(parse("thing"), "thing")

    def test_parse_program_accepts_multiple_expressions(self):
        self.assertEqual(parse_program("(define x 10) (+ x 5)"), [["define", "x", 10], ["+", "x", 5]])

    def test_parse_rejects_unmatched_parentheses(self):
        with self.assertRaises(LispSyntaxError):
            parse("(+ 1 2")

    def test_parse_rejects_extra_tokens(self):
        with self.assertRaises(LispSyntaxError):
            parse("(+ 1 2) 3")


if __name__ == "__main__":
    unittest.main()
