"""A2 fixer: Rewrite printer profile to U1 reference values."""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context

_reference: dict[str, Any] | None = None


def _load_reference() -> dict[str, Any]:
    global _reference
    if _reference is None:
        ref_file = resources.files("u1kit.data").joinpath("u1_printer_reference.json")
        _reference = json.loads(ref_file.read_text(encoding="utf-8"))
    return _reference


class A2PrinterProfileFixer(Fixer):
    """Rewrite printer profile fields from u1_printer_reference.json."""

    @property
    def id(self) -> str:
        return "a2"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        ref = _load_reference()
        for key, value in ref.items():
            config[key] = value
