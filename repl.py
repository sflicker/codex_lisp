"""Interactive REPL for the basic Lisp interpreter."""

from __future__ import annotations

import sys
import termios
import tty

try:
    import readline
except ImportError:  # pragma: no cover - platform dependent
    readline = None  # type: ignore[assignment]

from interpreter import LispError, evaluate, parse, standard_env, stringify


PROMPT = "lisp> "
HIGHLIGHT_START = "\033[7m"
HIGHLIGHT_END = "\033[0m"

ParenFrame = tuple[int, str]


class _LineReader:
    def __init__(self) -> None:
        self.history: list[str] = []

    def read_line(
        self,
        prompt: str,
        prior_lines: list[str] | None = None,
        initial_text: str = "",
    ) -> str:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            return input(prompt)

        prior_lines = prior_lines or []
        buffer: list[str] = list(initial_text)
        cursor = len(buffer)
        history_index: int | None = None
        source_prefix = _source_prefix(prior_lines)
        line_start = len(source_prefix)
        stdin_fd = sys.stdin.fileno()
        original_attrs = termios.tcgetattr(stdin_fd)

        sys.stdout.write(prompt)
        sys.stdout.flush()
        if buffer:
            self._render(prompt, buffer, cursor, prior_lines, source_prefix, line_start)

        try:
            tty.setraw(stdin_fd)
            while True:
                char = sys.stdin.read(1)

                if char in {"\r", "\n"}:
                    self._render(
                        prompt,
                        buffer,
                        cursor,
                        prior_lines,
                        source_prefix,
                        line_start,
                        highlight=False,
                    )
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                    return "".join(buffer)

                if char == "\x04":
                    if not buffer:
                        raise EOFError
                    continue

                if char == "\x03":
                    raise KeyboardInterrupt

                if char in {"\x7f", "\b"}:
                    if cursor > 0:
                        del buffer[cursor - 1]
                        cursor -= 1
                elif char == "\x1b":
                    cursor, history_index = self._handle_escape(
                        buffer, cursor, history_index
                    )
                elif char.isprintable():
                    buffer.insert(cursor, char)
                    cursor += 1
                    history_index = None

                self._render(
                    prompt, buffer, cursor, prior_lines, source_prefix, line_start
                )
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, original_attrs)

    def add_history(self, source: str) -> None:
        if not source:
            return
        history_entry = " ".join(source.splitlines())
        self.history.append(history_entry)
        if readline is not None:
            readline.add_history(history_entry)

    def _handle_escape(
        self, buffer: list[str], cursor: int, history_index: int | None
    ) -> tuple[int, int | None]:
        sequence = sys.stdin.read(2)
        if sequence == "[D":
            return max(0, cursor - 1), history_index
        if sequence == "[C":
            return min(len(buffer), cursor + 1), history_index
        if sequence == "[A" and self.history:
            if history_index is None:
                history_index = len(self.history) - 1
            else:
                history_index = max(0, history_index - 1)
            buffer[:] = list(self.history[history_index])
            return len(buffer), history_index
        if sequence == "[B" and history_index is not None:
            history_index += 1
            if history_index >= len(self.history):
                buffer.clear()
                return 0, None
            buffer[:] = list(self.history[history_index])
            return len(buffer), history_index
        return cursor, history_index

    def _render(
        self,
        prompt: str,
        buffer: list[str],
        cursor: int,
        prior_lines: list[str],
        source_prefix: str,
        line_start: int,
        highlight: bool = True,
    ) -> None:
        line = "".join(buffer)
        if prior_lines:
            self._render_block(prior_lines, line, cursor, highlight)
            return

        if highlight:
            source = source_prefix + line
            display = _highlight_matching_parens(
                source,
                line_start + cursor,
                display_start=line_start,
                display_end=line_start + len(line),
            )
        else:
            display = line

        sys.stdout.write(f"\r\033[2K{prompt}{display}\r")
        if len(prompt) + cursor:
            sys.stdout.write(f"\033[{len(prompt) + cursor}C")
        sys.stdout.flush()

    def _render_block(
        self,
        prior_lines: list[str],
        current_line: str,
        cursor: int,
        highlight: bool,
    ) -> None:
        lines = [*prior_lines, current_line]
        prompts = _prompts_for_lines(lines)
        source = "\n".join(lines)
        current_line_index = len(lines) - 1
        current_cursor = len("\n".join(prior_lines)) + 1 + cursor

        sys.stdout.write("\r")
        if prior_lines:
            sys.stdout.write(f"\033[{len(prior_lines)}A")

        line_start = 0
        for index, (line, prompt) in enumerate(zip(lines, prompts)):
            line_end = line_start + len(line)
            if highlight:
                display = _highlight_matching_parens(
                    source,
                    current_cursor,
                    display_start=line_start,
                    display_end=line_end,
                )
            else:
                display = line

            sys.stdout.write(f"\r\033[2K{prompt}{display}")
            if index < current_line_index:
                sys.stdout.write("\n")
            line_start = line_end + 1

        sys.stdout.write("\r")
        if len(prompts[-1]) + cursor:
            sys.stdout.write(f"\033[{len(prompts[-1]) + cursor}C")
        sys.stdout.flush()


_LINE_READER = _LineReader()


def _source_prefix(lines: list[str]) -> str:
    if not lines:
        return ""
    return "\n".join(lines) + "\n"


def _prompts_for_lines(lines: list[str]) -> list[str]:
    prompts = [PROMPT]
    for index in range(1, len(lines)):
        prompts.append(" " * len(PROMPT))
    return prompts


def _paren_stack(source: str) -> list[ParenFrame] | None:
    """Return unmatched opening paren locations, or None if a close is extra."""
    stack: list[ParenFrame] = []
    column = 0
    line_start = 0
    in_comment = False

    for index, char in enumerate(source):
        if char == "\n":
            column = 0
            line_start = index + 1
            in_comment = False
            continue

        if in_comment:
            column += 1
            continue

        if char == ";":
            in_comment = True
        elif char == "(":
            line_end = source.find("\n", line_start)
            if line_end == -1:
                line_end = len(source)
            stack.append((column, source[line_start:line_end]))
        elif char == ")":
            if not stack:
                return None
            stack.pop()

        column += 1

    return stack


def _needs_more_input(source: str) -> bool:
    stack = _paren_stack(source)
    return stack is not None and len(stack) > 0


def _continuation_prompt(source: str) -> str:
    return " " * _continuation_indent(source)


def _continuation_indent(source: str) -> int:
    stack = _paren_stack(source)
    return _first_operand_column(*stack[-1]) if stack else 0


def _first_operand_column(open_paren_column: int, line: str) -> int:
    index = open_paren_column + 1

    while index < len(line) and line[index].isspace():
        index += 1
    while index < len(line) and not line[index].isspace() and line[index] not in "()'":
        index += 1
    while index < len(line) and line[index].isspace():
        index += 1

    return index


def _matching_paren_indexes(source: str, cursor: int) -> tuple[int, int] | None:
    paren_index: int | None = None
    if cursor > 0 and source[cursor - 1] in "()":
        paren_index = cursor - 1
    elif cursor < len(source) and source[cursor] in "()":
        paren_index = cursor

    if paren_index is None:
        return None

    paren = source[paren_index]
    if paren == "(":
        depth = 0
        for index in range(paren_index, len(source)):
            if source[index] == "(":
                depth += 1
            elif source[index] == ")":
                depth -= 1
                if depth == 0:
                    return paren_index, index
    else:
        depth = 0
        for index in range(paren_index, -1, -1):
            if source[index] == ")":
                depth += 1
            elif source[index] == "(":
                depth -= 1
                if depth == 0:
                    return index, paren_index

    return None


def _highlight_matching_parens(
    source: str,
    cursor: int,
    display_start: int = 0,
    display_end: int | None = None,
) -> str:
    if display_end is None:
        display_end = len(source)

    matches = _matching_paren_indexes(source, cursor)
    display = source[display_start:display_end]
    if matches is None:
        return display

    highlighted: list[str] = []
    for index, char in enumerate(display, start=display_start):
        if index in matches:
            highlighted.append(f"{HIGHLIGHT_START}{char}{HIGHLIGHT_END}")
        else:
            highlighted.append(char)
    return "".join(highlighted)


def _read_expression() -> str | None:
    try:
        line = _LINE_READER.read_line(PROMPT)
    except EOFError:
        print()
        return None

    lines = [line]
    while _needs_more_input("\n".join(lines)):
        source = "\n".join(lines)
        indent = " " * _continuation_indent(source)
        try:
            lines.append(
                _LINE_READER.read_line(" " * len(PROMPT), lines, initial_text=indent)
            )
        except EOFError:
            print()
            return None

    return "\n".join(lines)


def _add_history(source: str) -> None:
    _LINE_READER.add_history(source)


def repl() -> None:
    env = standard_env()

    while True:
        source = _read_expression()
        if source is None:
            break

        if source.strip() in {"exit", "quit"}:
            break
        if not source.strip():
            continue

        _add_history(source)

        try:
            result = evaluate(parse(source), env)
        except LispError as exc:
            print(f"error: {exc}")
            continue

        if result is not None:
            print(stringify(result))


if __name__ == "__main__":
    repl()
