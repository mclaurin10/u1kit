"""Tests for the u1kit.interactive prompt module."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from u1kit.fixers.base import Fixer
from u1kit.interactive import FixAction, prompt_fix, render_diff_preview
from u1kit.rules.base import Context, Result, Severity


@dataclass
class _DummyFixer(Fixer):
    """Minimal Fixer stub so prompt_fix can read an id."""

    _id: str = "a2"

    @property
    def id(self) -> str:
        return self._id

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        return None


def _result(
    rule_id: str = "A2",
    fixer_id: str = "a2",
    diff_preview: str | None = None,
    severity: Severity = Severity.FAIL,
) -> Result:
    return Result(
        rule_id=rule_id,
        severity=severity,
        message="profile wrong",
        fixer_id=fixer_id,
        diff_preview=diff_preview,
    )


class TestRenderDiffPreview:
    def test_none_returns_empty(self) -> None:
        assert render_diff_preview(None) == ""

    def test_empty_returns_empty(self) -> None:
        assert render_diff_preview("") == ""

    def test_arrow_style_becomes_two_column(self) -> None:
        out = render_diff_preview("printer_settings_id: 'Bambu' -> 'U1'")
        assert "- " in out
        assert "+ " in out
        assert "Bambu" in out
        assert "U1" in out

    def test_multi_line_arrow(self) -> None:
        out = render_diff_preview(
            "printer_settings_id: 'Bambu' -> 'U1'\n"
            "printer_model: 'X1' -> 'Snapmaker U1'"
        )
        lines = out.splitlines()
        assert any(line.startswith("- ") and "Bambu" in line for line in lines)
        assert any(line.startswith("+ ") and "Snapmaker U1" in line for line in lines)

    def test_plain_text_gets_header(self) -> None:
        out = render_diff_preview("Removed 3 Bambu-specific macros")
        assert "Removed 3 Bambu-specific macros" in out


class TestPromptFix:
    def test_apply_returns_apply(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "a")
        action = prompt_fix(_result(), _DummyFixer())
        assert action is FixAction.APPLY

    def test_skip_returns_skip(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "s")
        action = prompt_fix(_result(), _DummyFixer())
        assert action is FixAction.SKIP

    def test_quit_returns_quit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "q")
        action = prompt_fix(_result(), _DummyFixer())
        assert action is FixAction.QUIT

    def test_edit_hook_accepted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "e")

        calls: list[tuple[Result, Fixer]] = []

        def hook(result: Result, fixer: Fixer) -> bool:
            calls.append((result, fixer))
            return True

        action = prompt_fix(_result(), _DummyFixer(), edit_hook=hook)
        assert action is FixAction.APPLY
        assert len(calls) == 1

    def test_edit_hook_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "e")
        action = prompt_fix(
            _result(), _DummyFixer(), edit_hook=lambda r, f: False
        )
        assert action is FixAction.SKIP
