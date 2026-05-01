"""Interactive REPL for the basic Lisp interpreter."""

from __future__ import annotations

from interpreter import LispError, evaluate, parse, standard_env, stringify


PROMPT = "lisp> "


def repl() -> None:
    env = standard_env()

    while True:
        try:
            line = input(PROMPT)
        except EOFError:
            print()
            break

        if line.strip() in {"exit", "quit"}:
            break
        if not line.strip():
            continue

        try:
            result = evaluate(parse(line), env)
        except LispError as exc:
            print(f"error: {exc}")
            continue

        if result is not None:
            print(stringify(result))


if __name__ == "__main__":
    repl()
