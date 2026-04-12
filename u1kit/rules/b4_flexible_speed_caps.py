"""B4: Flexible filaments need a conservative volumetric speed cap.

Flexibles (TPU, PEBA, TPE) misprint catastrophically when pushed at rigid-
PLA volumetric flow rates. The safest mechanical cap on Snapmaker U1 is
~5 mm^3/s; above 8 mm^3/s we emit a warning because the default Orca
profile for Generic PLA (20 mm^3/s) will be applied otherwise.
"""

from __future__ import annotations

from u1kit.filaments import (
    get_filament_field,
    get_used_filament_indices,
    is_flexible,
)
from u1kit.rules.base import Context, Result, Rule, Severity

FLEX_MAX_VOL_WARN_ABOVE = 8.0
FLEX_MAX_VOL_DEFAULT = 5.0


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class B4FlexibleSpeedCaps(Rule):
    """Flag used flex filaments without an adequate volumetric speed cap."""

    @property
    def id(self) -> str:
        return "B4"

    @property
    def name(self) -> str:
        return "Flexible filament speed caps"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)

        affected: list[str] = []
        for i in used:
            ftype = get_filament_field(config, "filament_type", i)
            if not is_flexible(ftype):
                continue
            current = get_filament_field(config, "filament_max_volumetric_speed", i)
            parsed = _parse_float(current)
            if parsed is None or parsed <= 0 or parsed > FLEX_MAX_VOL_WARN_ABOVE:
                affected.append(
                    f"Filament {i + 1} ({ftype}): "
                    f"filament_max_volumetric_speed={current!r}"
                )

        if not affected:
            return []

        diff = "\n".join(affected)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.WARN,
                message=(
                    "Flexible filament without adequate volumetric speed cap:\n"
                    + diff
                ),
                fixer_id="b4",
                diff_preview=diff,
            )
        ]
