"""C1 fixer: normalize conflicting bed-temp fields to min() across used slots.

For every ``*_plate_temp`` array where the used-set has mixed values, sets all
used indices to the minimum observed value (the safest compromise — the cooler
filament dictates). Unused slots are preserved so a future re-add of an unused
filament doesn't quietly lose data.
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
from u1kit.rules.c1_bed_temp_conflict import BED_TEMP_FIELDS


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class C1BedTempConflictFixer(Fixer):
    """Set each conflicting bed-temp field to min() across used slots."""

    @property
    def id(self) -> str:
        return "c1"

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
        if len(used) < 2:
            return

        for field in BED_TEMP_FIELDS:
            if field not in config:
                continue
            raw = [get_filament_field(config, field, i) for i in used]
            distinct = {v for v in raw if v is not None}
            if len(distinct) < 2:
                continue
            numeric = [v for v in (_parse_float(x) for x in raw) if v is not None]
            if not numeric:
                continue
            target = f"{min(numeric):g}"
            values = broadcast_field(config, field, count, target)
            for i in used:
                values[i] = target
            config[field] = values
