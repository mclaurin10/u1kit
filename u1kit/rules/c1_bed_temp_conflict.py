"""C1: bed-temperature conflict across used filaments on Snapmaker U1.

Snapmaker U1 has a single bed; every filament in use on a plate has to agree on
its bed-temperature target or the hotter-running filament will deform while the
cooler one is pushed. The per-filament ``*_plate_temp`` fields on
``project_settings.config`` are parallel arrays; conflict means ≥2 distinct
values among the indices actually referenced by the filament selectors.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

BED_TEMP_FIELDS: tuple[str, ...] = (
    "hot_plate_temp",
    "textured_plate_temp",
    "cool_plate_temp",
    "eng_plate_temp",
    "supertack_plate_temp",
    "textured_cool_plate_temp",
)


class C1BedTempConflict(Rule):
    """Flag ≥2 distinct bed-temp values among used filaments."""

    @property
    def id(self) -> str:
        return "C1"

    @property
    def name(self) -> str:
        return "Bed temperature conflict"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)
        if len(used) < 2:
            return []

        conflicts: list[str] = []
        for field in BED_TEMP_FIELDS:
            if field not in config:
                continue
            values = [get_filament_field(config, field, i) for i in used]
            distinct = {v for v in values if v is not None}
            if len(distinct) >= 2:
                conflicts.append(
                    f"{field}: used slots have {sorted(distinct)}"
                )

        if not conflicts:
            return []

        diff = "\n".join(conflicts)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=(
                    "Bed temperature conflict across used filaments:\n" + diff
                ),
                fixer_id="c1",
                diff_preview=diff,
            )
        ]
