"""C2 fixer: first-layer bed-temp min + 65°C cap on textured-PEI arrays.

Sets every used slot of a ``*_plate_temp_initial_layer`` field to the minimum
observed value among used slots. For the textured fields, additionally caps
the target at 65°C (Snapmaker U1 textured-PEI safe ceiling). Unused slots are
preserved.
"""

from __future__ import annotations

from typing import Any

from u1kit.filaments import (
    broadcast_field,
    get_filament_count,
    get_filament_field,
    get_used_filament_indices,
)
from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context
from u1kit.rules.c2_first_layer_bed_temp import (
    FIRST_LAYER_BED_TEMP_FIELDS,
    TEXTURED_INITIAL_FIELDS,
    TEXTURED_PEI_CAP,
)


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class C2FirstLayerBedTempFixer(Fixer):
    """Normalize used first-layer bed-temp slots, with textured-PEI 65°C cap."""

    @property
    def id(self) -> str:
        return "c2"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        count = get_filament_count(config)
        if count == 0:
            return
        used = get_used_filament_indices(config)
        if not used:
            return

        for field in FIRST_LAYER_BED_TEMP_FIELDS:
            if field not in config:
                continue
            raw = [get_filament_field(config, field, i) for i in used]
            numeric = [v for v in (_parse_float(x) for x in raw) if v is not None]
            if not numeric:
                continue
            distinct = {v for v in raw if v is not None}
            is_textured = field in TEXTURED_INITIAL_FIELDS
            needs_cap = is_textured and max(numeric) > TEXTURED_PEI_CAP
            if len(distinct) < 2 and not needs_cap:
                continue

            target_val = min(numeric)
            if is_textured:
                target_val = min(target_val, TEXTURED_PEI_CAP)
            target = f"{target_val:g}"

            values = broadcast_field(config, field, count, target)
            for i in used:
                values[i] = target
            config[field] = values
