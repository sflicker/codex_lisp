# Basic Lisp Interpreter

A small Lisp interpreter written in Python. It includes a tokenizer, parser,
evaluator, lexical environments, user-defined functions, and an interactive
REPL.

## Features

- Integer, float, boolean, and symbol parsing
- Lisp-style list expressions
- Arithmetic operators: `+`, `-`, `*`, `/`
- Comparisons: `=`, `<`, `>`, `<=`, `>=`
- Boolean literals and operators: `#t`, `#f`, `and`, `or`, `not`
- Variables with `define`
- Procedure definition shorthand: `(define (name arg ...) body ...)`
- Conditionals with `if`
- Multi-branch conditionals with `cond`
- Local bindings with `let`
- Functions with `lambda`
- Lexical closures
- Quoted symbols and lists with `quote` and `'`
- List primitives: `cons`, `car`, `cdr`, `list`, `null?`, `pair?`, `list?`,
  `append`, `length`
- Program execution with multiple expressions
- REPL-friendly error messages

## Project Layout

```text
.
├── interpreter.py
├── repl.py
├── lisp-plan.md
└── tests
    ├── test_eval.py
    └── test_parser.py
```

- `interpreter.py` contains the tokenizer, parser, evaluator, environment,
  built-ins, and public API.
- `repl.py` provides an interactive command-line REPL.
- `tests/` contains parser and evaluator unit tests.
- `lisp-plan.md` documents the original implementation plan and possible
  future extensions.

## Requirements

- Python 3.10 or newer

The project uses only the Python standard library.

## Running the REPL

```bash
python3 repl.py
```

Example session:

```text
lisp> (+ 1 2)
3
lisp> (define x 10)
x
lisp> (+ x 5)
15
lisp> (define square (lambda (x) (* x x)))
square
lisp> (square 9)
81
```

Exit with `exit`, `quit`, or `Ctrl-D`.

## Using the Interpreter from Python

```python
from interpreter import evaluate, parse, run, standard_env

env = standard_env()

print(evaluate(parse("(+ 1 (* 2 3))"), env))
print(run("(define x 10) (+ x 5)", env))
```

## Supported Lisp Examples

Arithmetic:

```lisp
(+ 1 2 3)
(- 10 3 2)
(* 3 4)
(/ 20 2 2)
```

Variables:

```lisp
(define radius 5)
(* 3.14 (* radius radius))
```

Conditionals:

```lisp
(if (> 3 2) 1 0)
(if #t 1 0)
(cond ((< 3 2) 0)
      (else 1))
```

Booleans:

```lisp
(and #t (> 3 2))
(or #f (< 3 2))
(not #f)
```

Functions:

```lisp
(define triple (lambda (x) (* x 3)))
(triple 7)
(define (square x) (* x x))
(square 9)
```

Local bindings:

```lisp
(let ((x 2)
      (y 3))
  (+ x y))
```

Lists and quoted data:

```lisp
'(a b c)
(list 1 2 3)
(car '(1 2 3))
(cdr '(1 2 3))
(cons 1 '(2 3))
```

Comments begin with `;` and continue to the end of the line.

## Running Tests

```bash
python3 -m unittest discover -s tests
```

## Current Limitations

This interpreter intentionally implements a small Lisp subset. It does not yet
include strings, dotted pairs, mutation, recursion helpers, file loading, or
multiline REPL input.
# codex_lisp
