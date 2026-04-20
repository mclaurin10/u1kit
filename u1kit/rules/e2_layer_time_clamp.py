"""E2: info when the estimated per-layer print time is below the cooling minimum.

On small plates, the single-layer extrusion volume is tiny, so even at the
slowest used filament's ``filament_max_volumetric_speed`` a layer prints in
under ``slow_down_layer_time``. Orca then clamps speed to
``slow_down_min_speed`` regardless of any "fast" settings the user thought
they were applying. This is the classic "my settings don't do anything"
symptom on small tall parts. Info-only — the user decides whether to raise
volumetric speed, lower the cooling minimum, or accept the clamp.

Formula (DECISIONS.md item 21):

    layer_volume_mm3  = plate_footprint_mm² × layer_height
    min_layer_time_s  = layer_volume_mm3 / min(filament_max_volumetric_speed[used])

Emit when ``min_layer_time_s < max(slow_down_layer_time[used])``. The
volumetric speed is the slowest used filament's cap; dividing layer volume
by that cap gives the tightest-achievable per-layer time. When that lower
bound is already below the cooling minimum, any "fast" setting the user
thought they were applying is academic — the slow-down will dominate.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.geometry import total_plate_footprint
from u1kit.rules.base import Context, Result, Rule, Severity

LAYER_HEIGHT_FIELD = "layer_height"
VMAX_FIELD = "filament_max_volumetric_speed"
SLOW_DOWN_FIELD = "slow_down_layer_time"


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


class E2LayerTimeClamp(Rule):
    """Info when cooling minimum will dominate actual print speed."""

    @property
    def id(self) -> str:
        return "E2"

    @property
    def name(self) -> str:
        return "Estimated layer time below cooling minimum"

    def check(self, context: Context) -> list[Result]:
        if context.geometry_bounds is None or not context.geometry_bounds:
            return []

        width, height = total_plate_footprint(context.geometry_bounds)
        plate_area = width * height
        if plate_area <= 0:
            return []

        layer_height = _parse_float(context.config.get(LAYER_HEIGHT_FIELD))
        if layer_height is None or layer_height <= 0:
            return []

        used = get_used_filament_indices(context.config)
        if not used:
            return []

        vmax_used: list[float] = []
        for i in used:
            raw = get_filament_field(context.config, VMAX_FIELD, i)
            parsed = _parse_float(raw)
            if parsed is not None and parsed > 0:
                vmax_used.append(parsed)
        if not vmax_used:
            return []

        slow_down_used: list[float] = []
        for i in used:
            raw = get_filament_field(context.config, SLOW_DOWN_FIELD, i)
            parsed = _parse_float(raw)
            if parsed is not None:
                slow_down_used.append(parsed)
        if not slow_down_used:
            return []

        min_vmax = min(vmax_used)
        max_slow_down = max(slow_down_used)
        layer_volume = plate_area * layer_height
        min_layer_time = layer_volume / min_vmax

        if min_layer_time >= max_slow_down:
            return []

        return [
            Result(
                rule_id=self.id,
                severity=Severity.INFO,
                message=(
                    f"Estimated layer time ({min_layer_time:.1f}s) is below "
                    f"the cooling minimum ({max_slow_down:.0f}s); "
                    f"slow_down_min_speed will dominate actual print speed."
                ),
                fixer_id=None,
                diff_preview=None,
            )
        ]
