"""A small Lisp interpreter with parsing, evaluation, and a REPL-friendly API."""

from __future__ import annotations

import math
import operator
from dataclasses import dataclass
from functools import reduce
from typing import Any, Callable, Iterable


Symbol = str
Expression = int | float | bool | Symbol | list[Any]


class LispError(Exception):
    """Base class for readable interpreter errors."""


class LispSyntaxError(LispError):
    """Raised when source text cannot be parsed as Lisp."""


class LispNameError(LispError):
    """Raised when a symbol is not bound in the current environment."""


class LispEvaluationError(LispError):
    """Raised when an expression is valid syntax but cannot be evaluated."""


class Env(dict[str, Any]):
    """A chained mapping for lexical scope."""

    def __init__(self, bindings: dict[str, Any] | None = None, parent: "Env | None" = None):
        super().__init__(bindings or {})
        self.parent = parent

    def find(self, name: str) -> "Env":
        if name in self:
            return self
        if self.parent is not None:
            return self.parent.find(name)
        raise LispNameError(f"unknown symbol: {name}")

    def get(self, name: str) -> Any:
        return self.find(name)[name]


@dataclass
class Procedure:
    params: list[str]
    body: list[Expression]
    env: Env

    def __call__(self, *args: Any) -> Any:
        if len(args) != len(self.params):
            raise LispEvaluationError(
                f"expected {len(self.params)} argument(s), got {len(args)}"
            )

        local_env = Env(dict(zip(self.params, args)), self.env)
        result: Any = None
        for expr in self.body:
            result = evaluate(expr, local_env)
        return result


def tokenize(source: str) -> list[str]:
    """Convert Lisp source text into tokens."""
    tokens: list[str] = []
    token = []
    in_comment = False

    for char in source:
        if in_comment:
            if char == "\n":
                in_comment = False
            continue

        if char == ";":
            if token:
                tokens.append("".join(token))
                token.clear()
            in_comment = True
            continue

        if char in "()'":
            if token:
                tokens.append("".join(token))
                token.clear()
            tokens.append(char)
        elif char.isspace():
            if token:
                tokens.append("".join(token))
                token.clear()
        else:
            token.append(char)

    if token:
        tokens.append("".join(token))

    return tokens


def parse(source: str) -> Expression:
    """Parse exactly one Lisp expression."""
    tokens = tokenize(source)
    if not tokens:
        raise LispSyntaxError("empty input")

    expr, next_index = _read_from_tokens(tokens, 0)
    if next_index != len(tokens):
        raise LispSyntaxError(f"unexpected token: {tokens[next_index]}")
    return expr


def parse_program(source: str) -> list[Expression]:
    """Parse zero or more Lisp expressions from source text."""
    tokens = tokenize(source)
    expressions: list[Expression] = []
    index = 0

    while index < len(tokens):
        expr, index = _read_from_tokens(tokens, index)
        expressions.append(expr)

    return expressions


def _read_from_tokens(tokens: list[str], index: int) -> tuple[Expression, int]:
    if index >= len(tokens):
        raise LispSyntaxError("unexpected end of input")

    token = tokens[index]

    if token == "(":
        values: list[Expression] = []
        index += 1
        while index < len(tokens) and tokens[index] != ")":
            value, index = _read_from_tokens(tokens, index)
            values.append(value)

        if index >= len(tokens):
            raise LispSyntaxError("unmatched '('")
        return values, index + 1

    if token == ")":
        raise LispSyntaxError("unexpected ')'")

    if token == "'":
        quoted, next_index = _read_from_tokens(tokens, index + 1)
        return ["quote", quoted], next_index

    return _atom(token), index + 1


def _atom(token: str) -> Expression:
    if token == "#t":
        return True
    if token == "#f":
        return False

    try:
        return int(token)
    except ValueError:
        pass

    try:
        return float(token)
    except ValueError:
        return Symbol(token)


def standard_env() -> Env:
    env = Env()
    env.update(
        {
            "+": lambda *args: sum(args),
            "-": _subtract,
            "*": _multiply,
            "/": _divide,
            "=": _compare(operator.eq),
            "<": _compare(operator.lt),
            ">": _compare(operator.gt),
            "<=": _compare(operator.le),
            ">=": _compare(operator.ge),
            "abs": abs,
            "max": max,
            "min": min,
            "round": round,
            "sqrt": math.sqrt,
            "print": _print,
            "cons": _cons,
            "car": _car,
            "cdr": _cdr,
            "list": lambda *args: list(args),
            "null?": lambda value: value == [],
            "pair?": lambda value: isinstance(value, list) and len(value) > 0,
            "list?": lambda value: isinstance(value, list),
            "append": _append,
            "length": _length,
        }
    )
    return env


def evaluate(expr: Expression, env: Env | None = None) -> Any:
    """Evaluate a parsed Lisp expression."""
    if env is None:
        env = standard_env()

    if isinstance(expr, (int, float, bool)):
        return expr

    if isinstance(expr, str):
        return env.get(expr)

    if not isinstance(expr, list):
        raise LispEvaluationError(f"cannot evaluate expression: {expr!r}")

    if not expr:
        raise LispEvaluationError("cannot evaluate empty list")

    first = expr[0]

    if first == "define":
        if len(expr) < 3:
            raise LispSyntaxError("define expects a name and value")

        target = expr[1]
        if isinstance(target, list):
            if not target:
                raise LispSyntaxError("define expects a procedure name")
            name = target[0]
            params = target[1:]
            if not isinstance(name, str):
                raise LispSyntaxError("define expects a symbol name")
            _validate_params(params, "define")
            env[name] = Procedure(params, expr[2:], env)
            return name

        if len(expr) != 3:
            raise LispSyntaxError("define variable form expects a single value")
        if not isinstance(target, str):
            raise LispSyntaxError("define expects a symbol name")
        env[target] = evaluate(expr[2], env)
        return target

    if first == "quote":
        _require_form_length(expr, 2, "quote")
        return expr[1]

    if first == "begin":
        return _eval_sequence(expr[1:], env)

    if first == "if":
        _require_form_length(expr, 4, "if")
        _, test, consequent, alternative = expr
        return evaluate(consequent if _truthy(evaluate(test, env)) else alternative, env)

    if first == "cond":
        return _eval_cond(expr[1:], env)

    if first == "let":
        return _eval_let(expr, env)

    if first == "and":
        result: Any = True
        for arg in expr[1:]:
            result = evaluate(arg, env)
            if not _truthy(result):
                return False
        return result

    if first == "or":
        for arg in expr[1:]:
            result = evaluate(arg, env)
            if _truthy(result):
                return result
        return False

    if first == "not":
        _require_form_length(expr, 2, "not")
        return not _truthy(evaluate(expr[1], env))

    if first == "lambda":
        if len(expr) < 3:
            raise LispSyntaxError("lambda expects parameters and a body")
        params = expr[1]
        if not isinstance(params, list):
            raise LispSyntaxError("lambda parameters must be a list of symbols")
        _validate_params(params, "lambda")
        return Procedure(params, expr[2:], env)

    proc = evaluate(first, env)
    args = [evaluate(arg, env) for arg in expr[1:]]

    if not callable(proc):
        raise LispEvaluationError(f"cannot call non-function: {stringify(proc)}")

    try:
        return proc(*args)
    except TypeError as exc:
        raise LispEvaluationError(str(exc)) from exc


def run(source: str, env: Env | None = None) -> Any:
    """Parse and evaluate all expressions in source, returning the last result."""
    if env is None:
        env = standard_env()

    result: Any = None
    for expr in parse_program(source):
        result = evaluate(expr, env)
    return result


def stringify(value: Any) -> str:
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is None:
        return "nil"
    if isinstance(value, list):
        return "(" + " ".join(stringify(item) for item in value) + ")"
    return str(value)


def _require_form_length(expr: list[Any], length: int, name: str) -> None:
    if len(expr) != length:
        raise LispSyntaxError(f"{name} expects {length - 1} argument(s)")


def _validate_params(params: list[Any], name: str) -> None:
    if not all(isinstance(p, str) for p in params):
        raise LispSyntaxError(f"{name} parameters must be symbols")
    if len(params) != len(set(params)):
        raise LispSyntaxError(f"{name} parameters must be unique")


def _eval_sequence(expressions: list[Expression], env: Env) -> Any:
    if not expressions:
        raise LispSyntaxError("expected at least one expression")

    result: Any = None
    for expression in expressions:
        result = evaluate(expression, env)
    return result


def _eval_cond(clauses: list[Expression], env: Env) -> Any:
    for index, clause in enumerate(clauses):
        if not isinstance(clause, list) or not clause:
            raise LispSyntaxError("cond clauses must be non-empty lists")

        test = clause[0]
        if test == "else":
            if index != len(clauses) - 1:
                raise LispSyntaxError("else must be the final cond clause")
            if len(clause) == 1:
                raise LispSyntaxError("else clause expects a result expression")
            return _eval_sequence(clause[1:], env)

        test_value = evaluate(test, env)
        if _truthy(test_value):
            if len(clause) == 1:
                return test_value
            return _eval_sequence(clause[1:], env)

    return None


def _eval_let(expr: list[Any], env: Env) -> Any:
    if len(expr) < 3:
        raise LispSyntaxError("let expects bindings and a body")

    bindings = expr[1]
    if not isinstance(bindings, list):
        raise LispSyntaxError("let bindings must be a list")

    names: list[str] = []
    values: list[Any] = []
    for binding in bindings:
        if not isinstance(binding, list) or len(binding) != 2:
            raise LispSyntaxError("let bindings must be (name value) pairs")
        name, value_expr = binding
        if not isinstance(name, str):
            raise LispSyntaxError("let binding names must be symbols")
        names.append(name)
        values.append(evaluate(value_expr, env))

    if len(names) != len(set(names)):
        raise LispSyntaxError("let binding names must be unique")

    return _eval_sequence(expr[2:], Env(dict(zip(names, values)), env))


def _truthy(value: Any) -> bool:
    return value is not False and value is not None


def _subtract(*args: float) -> float:
    _require_min_args(args, 1, "-")
    if len(args) == 1:
        return -args[0]
    return reduce(operator.sub, args)


def _multiply(*args: float) -> float:
    return reduce(operator.mul, args, 1)


def _divide(*args: float) -> float:
    _require_min_args(args, 1, "/")
    if len(args) == 1:
        return 1 / args[0]
    return reduce(operator.truediv, args)


def _compare(op: Callable[[Any, Any], bool]) -> Callable[..., bool]:
    def compare(*args: Any) -> bool:
        _require_min_args(args, 2, "comparison")
        return all(op(left, right) for left, right in _pairs(args))

    return compare


def _pairs(values: Iterable[Any]) -> Iterable[tuple[Any, Any]]:
    iterator = iter(values)
    previous = next(iterator)
    for current in iterator:
        yield previous, current
        previous = current


def _require_min_args(args: tuple[Any, ...], minimum: int, name: str) -> None:
    if len(args) < minimum:
        raise LispEvaluationError(f"{name} expects at least {minimum} argument(s)")


def _require_arg_count(args: tuple[Any, ...], count: int, name: str) -> None:
    if len(args) != count:
        raise LispEvaluationError(f"{name} expects {count} argument(s)")


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise LispEvaluationError(f"{name} expects a list")
    return value


def _cons(*args: Any) -> list[Any]:
    _require_arg_count(args, 2, "cons")
    rest = _require_list(args[1], "cons")
    return [args[0], *rest]


def _car(*args: Any) -> Any:
    _require_arg_count(args, 1, "car")
    values = _require_list(args[0], "car")
    if not values:
        raise LispEvaluationError("car expects a non-empty list")
    return values[0]


def _cdr(*args: Any) -> list[Any]:
    _require_arg_count(args, 1, "cdr")
    values = _require_list(args[0], "cdr")
    if not values:
        raise LispEvaluationError("cdr expects a non-empty list")
    return values[1:]


def _append(*args: Any) -> list[Any]:
    result: list[Any] = []
    for value in args:
        result.extend(_require_list(value, "append"))
    return result


def _length(*args: Any) -> int:
    _require_arg_count(args, 1, "length")
    return len(_require_list(args[0], "length"))


def _print(*args: Any) -> None:
    print(*(stringify(arg) for arg in args))


lisp_eval = evaluate
