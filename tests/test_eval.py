import io
import unittest
from contextlib import redirect_stdout

from interpreter import (
    LispEvaluationError,
    LispNameError,
    LispSyntaxError,
    evaluate,
    parse,
    run,
    standard_env,
)


class EvaluatorTests(unittest.TestCase):
    def setUp(self):
        self.env = standard_env()

    def eval(self, source):
        return evaluate(parse(source), self.env)

    def test_arithmetic(self):
        self.assertEqual(self.eval("(+ 1 2)"), 3)
        self.assertEqual(self.eval("(* 3 4)"), 12)
        self.assertEqual(self.eval("(- 10 3 2)"), 5)
        self.assertEqual(self.eval("(/ 20 2 2)"), 5)

    def test_variables(self):
        self.assertEqual(self.eval("(define x 10)"), "x")
        self.assertEqual(self.eval("(+ x 5)"), 15)

    def test_define_procedure_shorthand(self):
        self.assertEqual(self.eval("(define (square x) (* x x))"), "square")
        self.assertEqual(self.eval("(square 9)"), 81)

    def test_conditionals(self):
        self.assertEqual(self.eval("(if (> 3 2) 1 0)"), 1)
        self.assertEqual(self.eval("(if (< 3 2) 1 0)"), 0)
        self.assertEqual(self.eval("(if #t 1 0)"), 1)
        self.assertEqual(self.eval("(if #f 1 0)"), 0)

    def test_cond(self):
        self.assertEqual(self.eval("(cond ((< 2 1) 10) ((> 2 1) 20) (else 30))"), 20)
        self.assertEqual(self.eval("(cond ((< 2 1) 10) (else 30))"), 30)

    def test_let(self):
        self.eval("(define x 10)")
        self.assertEqual(self.eval("(let ((x 2) (y 3)) (+ x y))"), 5)
        self.assertEqual(self.eval("x"), 10)

    def test_begin(self):
        self.assertEqual(self.eval("(begin (define x 4) (+ x 6))"), 10)

    def test_boolean_operators(self):
        self.assertIs(self.eval("(and #t #t)"), True)
        self.assertIs(self.eval("(and #t #f)"), False)
        self.assertIs(self.eval("(or #f #t)"), True)
        self.assertIs(self.eval("(or #f #f)"), False)
        self.assertIs(self.eval("(not #t)"), False)
        self.assertIs(self.eval("(not #f)"), True)

    def test_boolean_operators_short_circuit(self):
        self.assertIs(self.eval("(and #f missing)"), False)
        self.assertIs(self.eval("(or #t missing)"), True)

    def test_lambdas_capture_environment(self):
        self.eval("(define scale 3)")
        self.eval("(define triple (lambda (x) (* x scale)))")
        self.assertEqual(self.eval("(triple 9)"), 27)

    def test_quote(self):
        self.assertEqual(self.eval("'x"), "x")
        self.assertEqual(self.eval("'(a b c)"), ["a", "b", "c"])
        self.assertEqual(self.eval("'()"), [])

    def test_list_primitives(self):
        self.assertEqual(self.eval("(list 1 2 3)"), [1, 2, 3])
        self.assertEqual(self.eval("(cons 1 '(2 3))"), [1, 2, 3])
        self.assertEqual(self.eval("(car '(1 2 3))"), 1)
        self.assertEqual(self.eval("(cdr '(1 2 3))"), [2, 3])
        self.assertEqual(self.eval("(append '(1 2) '(3 4))"), [1, 2, 3, 4])
        self.assertEqual(self.eval("(length '(1 2 3))"), 3)
        self.assertIs(self.eval("(null? '())"), True)
        self.assertIs(self.eval("(pair? '(1 2))"), True)
        self.assertIs(self.eval("(pair? '())"), False)
        self.assertIs(self.eval("(list? '(1 2))"), True)

    def test_nested_calls(self):
        self.assertEqual(self.eval("(+ 1 (* 2 3) (- 10 4))"), 13)

    def test_run_evaluates_multiple_expressions(self):
        self.assertEqual(run("(define x 10) (+ x 5)", self.env), 15)

    def test_print_builtin(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.eval("(print (+ 1 2))")
        self.assertEqual(output.getvalue(), "3\n")

    def test_unknown_symbol_error(self):
        with self.assertRaises(LispNameError):
            self.eval("missing")

    def test_wrong_argument_count_for_user_function(self):
        self.eval("(define id (lambda (x) x))")
        with self.assertRaises(LispEvaluationError):
            self.eval("(id 1 2)")

    def test_invalid_special_forms(self):
        with self.assertRaises(LispSyntaxError):
            self.eval("(if #t 1)")
        with self.assertRaises(LispSyntaxError):
            self.eval("(lambda x x)")

    def test_calling_non_function_error(self):
        with self.assertRaises(LispEvaluationError):
            self.eval("(1 2)")


if __name__ == "__main__":
    unittest.main()
