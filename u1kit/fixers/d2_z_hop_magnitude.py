"""D2 fixer: cap ``z_hop`` and zero ``filament_z_hop`` on tripping slots.

Target magnitude is ``min(1.5, 4 * layer_height)``. The spec comment in
phase-two.md suggests ``max(1.5, 4 * layer_height)`` but that leaves the
result above the 5x trigger for any layer_height >= 0.3 mm, so we use ``min``
— that keeps the target strictly below the trigger for all realistic layer
heights (0.05-1.5 mm).
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
from u1kit.rules.d2_z_hop_magnitude import (
    FILAMENT_Z_HOP_FIELD,
    Z_HOP_FIELD,
)


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class D2ZHopMagnitudeFixer(Fixer):
    """Cap z_hop and zero filament_z_hop on used slots that exceed 5x layer_height."""

    @property
    def id(self) -> str:
        return "d2"

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

        layer_height = _parse_float(config.get("layer_height"))
        if layer_height is None or layer_height <= 0:
            return

        trigger = 5 * layer_height
        target_str = f"{min(1.5, 4 * layer_height):g}"

        tripped: list[int] = []
        for i in used:
            z = _parse_float(get_filament_field(config, Z_HOP_FIELD, i)) or 0.0
            fz = _parse_float(
                get_filament_field(config, FILAMENT_Z_HOP_FIELD, i)
            ) or 0.0
            if max(z, fz) >= trigger:
                tripped.append(i)

        if not tripped:
            return

        z_values = broadcast_field(config, Z_HOP_FIELD, count, "0")
        fz_values = broadcast_field(config, FILAMENT_Z_HOP_FIELD, count, "0")

        for i in tripped:
            z = _parse_float(z_values[i]) or 0.0
            if z >= trigger:
                z_values[i] = target_str
            fz_values[i] = "0"

        config[Z_HOP_FIELD] = z_values
        config[FILAMENT_Z_HOP_FIELD] = fz_values
