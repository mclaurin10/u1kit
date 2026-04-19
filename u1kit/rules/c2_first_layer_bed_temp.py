"""C2: first-layer bed-temperature conflict, plus textured-PEI 65°C cap.

First-layer adhesion fails when used filaments disagree on the initial-layer
bed temperature; textured PEI additionally scorches above ~65°C, so even
uniform values need a safety ceiling. The canonical ``first_layer_bed_temperature``
field is absent on Snapmaker U1 native exports — C2 walks whichever
``*_plate_temp_initial_layer`` parallel arrays the config actually carries.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

FIRST_LAYER_BED_TEMP_FIELDS: tuple[str, ...] = (
    "hot_plate_temp_initial_layer",
    "textured_plate_temp_initial_layer",
    "cool_plate_temp_initial_layer",
    "eng_plate_temp_initial_layer",
    "supertack_plate_temp_initial_layer",
    "textured_cool_plate_temp_initial_layer",
)

TEXTURED_INITIAL_FIELDS: frozenset[str] = frozenset({
    "textured_plate_temp_initial_layer",
    "textured_cool_plate_temp_initial_layer",
})

TEXTURED_PEI_CAP = 65.0


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class C2FirstLayerBedTemp(Rule):
    """Flag first-layer bed-temp conflicts and textured-PEI > 65°C values."""

    @property
    def id(self) -> str:
        return "C2"

    @property
    def name(self) -> str:
        return "First-layer bed temperature conflict"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)
        if not used:
            return []

        issues: list[str] = []
        for field in FIRST_LAYER_BED_TEMP_FIELDS:
            if field not in config:
                continue
            raw = [get_filament_field(config, field, i) for i in used]
            distinct = {v for v in raw if v is not None}
            if len(distinct) >= 2:
                issues.append(f"{field}: used slots have {sorted(distinct)}")

            if field in TEXTURED_INITIAL_FIELDS:
                numeric = [v for v in (_parse_float(x) for x in raw) if v is not None]
                if numeric and max(numeric) > TEXTURED_PEI_CAP:
                    issues.append(
                        f"{field}: exceeds {TEXTURED_PEI_CAP:g}°C textured-PEI cap"
                    )

        if not issues:
            return []

        diff = "\n".join(issues)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message="First-layer bed temperature issues:\n" + diff,
                fixer_id="c2",
                diff_preview=diff,
            )
        ]
