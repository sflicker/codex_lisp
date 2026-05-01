# Basic Lisp Interpreter Plan

The goal is to create a basic Lisp interpreter in Python where users can enter Lisp commands and have them immediately executed through a REPL.

## 1. Define the Lisp Subset

Start with a small, useful Lisp:

- Numbers
- Symbols
- Lists
- Arithmetic: `+`, `-`, `*`, `/`
- Comparisons: `=`, `<`, `>`, `<=`, `>=`
- Variables with `define`
- Conditionals with `if`
- Functions with `lambda`
- Function calls
- A REPL for interactive execution

## 2. Represent Lisp Values in Python

Use simple Python types:

- Lisp numbers: Python `int` or `float`
- Lisp symbols: Python `str`
- Lisp lists: Python `list`
- Lisp functions: Python callables or a custom function object
- Lisp environments: chained dictionaries

## 3. Build a Tokenizer

Convert raw input text into tokens.

Example:

```lisp
(+ 1 (* 2 3))
```

becomes:

```python
["(", "+", "1", "(", "*", "2", "3", ")", ")"]
```

## 4. Build a Parser

Convert tokens into an abstract syntax tree using Python lists.

Example:

```lisp
(+ 1 (* 2 3))
```

becomes:

```python
["+", 1, ["*", 2, 3]]
```

## 5. Implement Environments

Create an `Env` class that stores bindings and optionally points to a parent environment.

This supports lexical scoping:

```lisp
(define x 10)
(+ x 5)
```

## 6. Add Built-in Functions

Populate the global environment with Python implementations of core Lisp functions:

```python
{
    "+": lambda *args: sum(args),
    "-": ...,
    "*": ...,
    "/": ...,
    "=": ...,
    "print": print,
}
```

## 7. Write the Evaluator

Implement `eval(expr, env)`.

It should handle:

- Number literals
- Symbol lookup
- `define`
- `if`
- `lambda`
- Function calls

Example:

```lisp
(+ 1 2)
```

Evaluation flow:

1. Look up `+`.
2. Evaluate `1`.
3. Evaluate `2`.
4. Call the Python function bound to `+`.

## 8. Implement User-defined Functions

Represent lambdas as closures that capture:

- Parameter names
- Function body
- Defining environment

Example:

```lisp
(define square
  (lambda (x)
    (* x x)))

(square 5)
```

## 9. Build the REPL

Add a loop that reads, parses, evaluates, and prints results:

```text
lisp> (+ 1 2)
3
lisp> (define x 10)
x
lisp> (+ x 5)
15
```

The REPL should:

- Read user input
- Parse it
- Evaluate it
- Print the result
- Continue until `exit` or `Ctrl-D`

## 10. Handle Errors Cleanly

Add readable errors for:

- Unmatched parentheses
- Unknown symbols
- Wrong argument counts
- Invalid syntax
- Calling non-functions

## 11. Add Tests

Cover:

- Tokenization
- Parsing
- Arithmetic
- Variable definitions
- Conditionals
- Lambdas
- Nested calls
- REPL-adjacent behavior

## 12. Suggested File Layout

```text
lisp/
  interpreter.py
  repl.py
  tests/
    test_parser.py
    test_eval.py
```

## 13. First Working Milestone

Aim for this to work first:

```lisp
(+ 1 2)
(* 3 4)
(define x 10)
(+ x 5)
```

## 14. Second Working Milestone

Add functions and conditionals:

```lisp
(if (> 3 2) 1 0)

(define square
  (lambda (x)
    (* x x)))

(square 9)
```

## 15. Later Extensions

Once the basic interpreter works, consider adding:

- Strings
- Booleans
- Lists as data
- `quote`
- `let`
- Recursion
- Tail-call optimization
- File loading
- Better multiline REPL input
