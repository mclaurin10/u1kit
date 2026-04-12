"""Interactive prompt module for the fix pipeline.

Handles rendering a Result + diff preview and asking the user whether to
apply, skip, or quit. Optional per-fixer `edit_hook` lets fixers like B1
collect richer interactive input (merge confirmations) without leaking
prompt logic into the CLI layer.

Click-only by design; prompt_toolkit is reserved for the Phase 3 GUI.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Protocol

import click

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Result


class FixAction(Enum):
    """Outcome of an interactive prompt."""

    APPLY = "apply"
    SKIP = "skip"
    QUIT = "quit"


class EditHook(Protocol):
    """Optional per-fixer editor invoked when the user picks `[e]dit`.

    Returns True to apply the (possibly-edited) fix, False to skip.
    """

    def __call__(self, result: Result, fixer: Fixer) -> bool: ...


EditCallback = Callable[[Result, Fixer], bool]


def render_diff_preview(diff_preview: str | None) -> str:
    """Render a Result.diff_preview as a human-readable block.

    If the preview contains ` -> ` pairs (Phase 1 style), split each line into
    a 2-column diff (`- <before>` / `+ <after>`). Otherwise emit the text
    unchanged. Returns an empty string for None/empty input.
    """
    if not diff_preview:
        return ""

    out_lines: list[str] = []
    for raw_line in diff_preview.splitlines():
        if " -> " in raw_line:
            before, after = raw_line.split(" -> ", 1)
            out_lines.append(f"- {before}")
            out_lines.append(f"+ {after}")
        else:
            out_lines.append(raw_line)
    return "\n".join(out_lines)


def prompt_fix(
    result: Result,
    fixer: Fixer,
    edit_hook: EditHook | None = None,
) -> FixAction:
    """Render the finding + preview and ask the user what to do.

    Choices: `[a]pply`, `[s]kip`, `[q]uit`. If `edit_hook` is provided, `[e]dit`
    is offered as an additional option and delegates to the hook; the hook's
    return value determines whether the action is APPLY or SKIP.
    """
    click.echo(f"\n[{result.rule_id}] {result.message}")
    preview = render_diff_preview(result.diff_preview)
    if preview:
        for line in preview.splitlines():
            click.echo(f"  {line}")

    choices = ["a", "s", "q"]
    hint = "[a]pply / [s]kip / [q]uit"
    if edit_hook is not None:
        choices.append("e")
        hint = "[a]pply / [s]kip / [q]uit / [e]dit"

    choice = click.prompt(
        f"  Fix '{fixer.id}'? {hint}",
        type=click.Choice(choices, case_sensitive=False),
        default="a",
        show_default=True,
        show_choices=False,
    )
    choice = str(choice).lower()

    if choice == "a":
        return FixAction.APPLY
    if choice == "s":
        return FixAction.SKIP
    if choice == "q":
        return FixAction.QUIT
    if choice == "e" and edit_hook is not None:
        return FixAction.APPLY if edit_hook(result, fixer) else FixAction.SKIP
    return FixAction.SKIP
