"""B4 fixer: inject conservative volumetric + wall-speed caps for flexibles.

Writes a safe ``filament_max_volumetric_speed`` for every used flex slot and
derives a per-filament wall/infill speed cap from
``max_vol / (line_width * layer_height) * 0.8``. Scalar speed fields are
broadcast to parallel arrays so the cap only affects the flex slots; rigid
slots inherit whatever the scalar was.
"""

from __future__ import annotations

from typing import Any

from u1kit.filaments import (
    broadcast_field,
    get_filament_count,
    get_filament_field,
    get_used_filament_indices,
    is_flexible,
)
from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context

CONSERVATIVE_FACTOR = 0.8
DEFAULT_LAYER_HEIGHT = 0.2
DEFAULT_LINE_WIDTH = 0.42
DEFAULT_WALL_SPEED = "60"
DEFAULT_INFILL_SPEED = "80"
FLEX_MAX_VOL_WARN_ABOVE = 8.0
FLEX_MAX_VOL_DEFAULT = 5.0

SPEED_FIELD_LINE_WIDTH: tuple[tuple[str, str, str], ...] = (
    ("outer_wall_speed", "outer_wall_line_width", DEFAULT_WALL_SPEED),
    ("inner_wall_speed", "inner_wall_line_width", DEFAULT_WALL_SPEED),
    ("sparse_infill_speed", "sparse_infill_line_width", DEFAULT_INFILL_SPEED),
)


def _parse_float(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class B4FlexibleSpeedCapsFixer(Fixer):
    """Write flex-safe volumetric + wall/infill speed caps per filament slot."""

    @property
    def id(self) -> str:
        return "b4"

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

        layer_height = _parse_float(config.get("layer_height"), DEFAULT_LAYER_HEIGHT)
        if layer_height <= 0:
            layer_height = DEFAULT_LAYER_HEIGHT

        max_vol = broadcast_field(
            config, "filament_max_volumetric_speed", count, "20"
        )
        for i in used:
            ftype = get_filament_field(config, "filament_type", i)
            if not is_flexible(ftype):
                continue
            current = _parse_float(max_vol[i], 0.0)
            if current <= 0 or current > FLEX_MAX_VOL_WARN_ABOVE:
                max_vol[i] = str(FLEX_MAX_VOL_DEFAULT)
        config["filament_max_volumetric_speed"] = max_vol

        for speed_field, width_field, speed_default in SPEED_FIELD_LINE_WIDTH:
            line_width = _parse_float(config.get(width_field), DEFAULT_LINE_WIDTH)
            if line_width <= 0:
                line_width = DEFAULT_LINE_WIDTH

            speeds = broadcast_field(config, speed_field, count, speed_default)

            for i in used:
                ftype = get_filament_field(config, "filament_type", i)
                if not is_flexible(ftype):
                    continue
                mv = _parse_float(max_vol[i], FLEX_MAX_VOL_DEFAULT)
                cap = (mv / (line_width * layer_height)) * CONSERVATIVE_FACTOR
                current_speed = _parse_float(speeds[i], 0.0)
                if current_speed <= 0 or current_speed > cap:
                    speeds[i] = f"{cap:.1f}"

            config[speed_field] = speeds
