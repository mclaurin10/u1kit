"""E3 fixer: bump prime_tower_brim_width to 5 mm when opt-in is declared.

The rule always emits warn-level guidance on small plates, but this fixer
only runs when a preset explicitly sets ``e3_auto_bump: true`` in its
``options:`` block. This keeps the default behavior conservative — the
bump costs filament and time — and makes it a deliberate preset choice
(e.g. ``peba-safe`` for flexible-filament prints where tower tipping is
more likely) rather than a surprise side effect of running ``u1kit fix``.
"""

from __future__ import annotations

from typing import Any

from u1kit.fixers.base import Fixer, FixerAbort
from u1kit.rules.base import Context
from u1kit.rules.e3_prime_tower_brim import BRIM_FIELD, BRIM_THRESHOLD_MM


class E3BrimBumpNotRequested(FixerAbort):
    """Raised when E3 is invoked without ``e3_auto_bump: true`` in options."""


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


class E3PrimeTowerBrimFixer(Fixer):
    """Bump prime_tower_brim_width to max(current, 5) mm when opted-in."""

    @property
    def id(self) -> str:
        return "e3"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        if not bool(context.options.get("e3_auto_bump")):
            raise E3BrimBumpNotRequested(
                "E3 brim bump requires opt-in via preset option 'e3_auto_bump'"
            )

        current = _parse_float(config.get(BRIM_FIELD)) or 0.0
        new_width = max(current, BRIM_THRESHOLD_MM)
        config[BRIM_FIELD] = str(new_width)
