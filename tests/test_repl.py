import unittest

from repl import (
    HIGHLIGHT_END,
    HIGHLIGHT_START,
    PROMPT,
    _highlight_matching_parens,
    _matching_paren_indexes,
    _continuation_indent,
    _continuation_prompt,
    _prompts_for_lines,
    _needs_more_input,
    _paren_stack,
)


class ReplInputTests(unittest.TestCase):
    def test_needs_more_input_for_missing_closing_paren(self):
        self.assertTrue(_needs_more_input("(+ 1 2"))

    def test_does_not_need_more_input_when_balanced(self):
        self.assertFalse(_needs_more_input("(+ 1 2)"))

    def test_does_not_treat_extra_closing_paren_as_continuation(self):
        self.assertIsNone(_paren_stack("(+ 1 2))"))
        self.assertFalse(_needs_more_input("(+ 1 2))"))

    def test_ignores_parentheses_in_comments(self):
        self.assertFalse(_needs_more_input("(+ 1 2) ; ("))

    def test_continuation_prompt_aligns_under_leftmost_operand(self):
        self.assertEqual(_continuation_prompt("(+ 1"), " " * 3)

    def test_nested_continuation_prompt_uses_innermost_open_paren(self):
        self.assertEqual(_continuation_prompt("(begin\n(+ 1"), " " * 3)
        self.assertEqual(_continuation_prompt("(begin\n  (+ 1"), " " * 5)

    def test_continuation_prompt_tracks_unclosed_form_across_lines(self):
        lines = [
            "(+ (* 3",
            "      (+ (* 2 4)",
            "         (+ 3 5)))",
            "   (+ (- 10 7)",
        ]

        self.assertEqual(_continuation_prompt("\n".join(lines[:1])), " " * 6)
        self.assertEqual(_continuation_prompt("\n".join(lines[:2])), " " * 9)
        self.assertEqual(_continuation_prompt("\n".join(lines[:3])), " " * 3)
        self.assertEqual(_continuation_prompt("\n".join(lines[:4])), " " * 6)

    def test_continuation_indent_uses_previous_generated_indentation(self):
        lines = ["(+ (* 3"]
        lines.append(" " * _continuation_indent("\n".join(lines)) + "(+ (* 2 4)")
        lines.append(" " * _continuation_indent("\n".join(lines)) + "(+ 3 5)))")
        lines.append(" " * _continuation_indent("\n".join(lines)) + "(+ (- 10 7)")

        self.assertEqual(lines, [
            "(+ (* 3",
            "      (+ (* 2 4)",
            "         (+ 3 5)))",
            "   (+ (- 10 7)",
        ])

    def test_displayed_continuation_lines_compensate_for_missing_prompt(self):
        lines = [
            "(+ (* 3",
            "      (+ (* 2 4)",
            "         (+ 3 5)))",
            "   (+ (- 10 7)",
            "      6))",
        ]
        prompts = _prompts_for_lines(lines)

        self.assertEqual([prompt + line for prompt, line in zip(prompts, lines)], [
            "lisp> (+ (* 3",
            "            (+ (* 2 4)",
            "               (+ 3 5)))",
            "         (+ (- 10 7)",
            "            6))",
        ])

    def test_finds_matching_parens_when_cursor_after_paren(self):
        self.assertEqual(_matching_paren_indexes("(+ 1 2)", 7), (0, 6))

    def test_finds_matching_parens_when_cursor_before_paren(self):
        self.assertEqual(_matching_paren_indexes("(+ 1 2)", 0), (0, 6))

    def test_highlights_matching_parens(self):
        self.assertEqual(
            _highlight_matching_parens("(+ 1 2)", 7),
            f"{HIGHLIGHT_START}({HIGHLIGHT_END}+ 1 2{HIGHLIGHT_START}){HIGHLIGHT_END}",
        )

    def test_highlights_current_line_when_match_is_on_prior_line(self):
        source = "(+ 1\n  2)"
        self.assertEqual(
            _highlight_matching_parens(
                source,
                len(source),
                display_start=len("(+ 1\n"),
                display_end=len(source),
            ),
            f"  2{HIGHLIGHT_START}){HIGHLIGHT_END}",
        )

    def test_highlights_prior_line_when_match_is_on_current_line(self):
        source = "(+ 1\n  2)"
        self.assertEqual(
            _highlight_matching_parens(
                source,
                len(source),
                display_start=0,
                display_end=len("(+ 1"),
            ),
            f"{HIGHLIGHT_START}({HIGHLIGHT_END}+ 1",
        )

    def test_does_not_highlight_unmatched_paren(self):
        self.assertEqual(_highlight_matching_parens("(+ 1 2", 0), "(+ 1 2")


if __name__ == "__main__":
    unittest.main()
