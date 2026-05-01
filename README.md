# Basic Lisp Interpreter

A small Lisp interpreter written in Python. It includes a tokenizer, parser,
evaluator, lexical environments, user-defined functions, and an interactive
REPL.

## Features

- Integer, float, boolean, and symbol parsing
- Lisp-style list expressions
- Arithmetic operators: `+`, `-`, `*`, `/`
- Comparisons: `=`, `<`, `>`, `<=`, `>=`
- Variables with `define`
- Conditionals with `if`
- Functions with `lambda`
- Lexical closures
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
```

Functions:

```lisp
(define triple (lambda (x) (* x 3)))
(triple 7)
```

Comments begin with `;` and continue to the end of the line.

## Running Tests

```bash
python3 -m unittest discover -s tests
```

## Current Limitations

This interpreter intentionally implements a small Lisp subset. It does not yet
include strings, quoted data, list manipulation primitives, `let`, recursion
helpers, file loading, or multiline REPL input.
# codex_lisp
