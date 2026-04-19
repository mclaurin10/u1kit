"""C3 fixer: set used slow_down_layer_time to max() across used slots."""

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
from u1kit.rules.c3_slow_down_layer_time import SLOW_DOWN_FIELD


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class C3SlowDownLayerTimeFixer(Fixer):
    """Set every used slow_down_layer_time slot to max() across used."""

    @property
    def id(self) -> str:
        return "c3"

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
        if SLOW_DOWN_FIELD not in config:
            return

        raw = [get_filament_field(config, SLOW_DOWN_FIELD, i) for i in used]
        distinct = {v for v in raw if v is not None}
        if len(distinct) < 2:
            return
        numeric = [v for v in (_parse_float(x) for x in raw) if v is not None]
        if not numeric:
            return

        target = f"{max(numeric):g}"
        values = broadcast_field(config, SLOW_DOWN_FIELD, count, target)
        for i in used:
            values[i] = target
        config[SLOW_DOWN_FIELD] = values
