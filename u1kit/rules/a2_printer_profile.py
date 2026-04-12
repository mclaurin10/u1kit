"""A2: Printer profile must match U1."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from u1kit.rules.base import Context, Result, Rule, Severity

_reference: dict[str, Any] | None = None


def _load_reference() -> dict[str, Any]:
    global _reference
    if _reference is None:
        ref_file = resources.files("u1kit.data").joinpath("u1_printer_reference.json")
        _reference = json.loads(ref_file.read_text(encoding="utf-8"))
    return _reference


# Keys that define the printer profile
PROFILE_KEYS = (
    "printer_settings_id",
    "printer_model",
)


class A2PrinterProfile(Rule):
    """Check that the printer profile is set to U1."""

    @property
    def id(self) -> str:
        return "A2"

    @property
    def name(self) -> str:
        return "Printer profile"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        ref = _load_reference()

        mismatches: list[str] = []
        for key in PROFILE_KEYS:
            current = config.get(key, "")
            expected = ref.get(key, "")
            if current != expected:
                mismatches.append(f"{key}: {current!r} -> {expected!r}")

        if not mismatches:
            return []

        diff = "\n".join(mismatches)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=f"Printer profile is not U1. Mismatched fields:\n{diff}",
                fixer_id="a2",
                diff_preview=diff,
            )
        ]
