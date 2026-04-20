"""E3: warn when prime_tower_brim_width is too thin for a small-plate layout.

On U1 native exports the prime tower is a single vertical column that can
tip over during toolchanges when its ground-plane footprint is small. Orca
lets you add a brim around the tower to counteract this; on full-bed prints
the default 0–3 mm brim is fine, but when the plate footprint is small the
tower sits near a plate edge where a wider brim is worth the filament cost.

Threshold (DECISIONS.md items 14, 22): plate bounding-box min dimension
below 120 mm AND ``prime_tower_brim_width`` below 5 mm AND a prime tower
is actually in use. Severity warn, with an opt-in fixer gated by
``e3_auto_bump: true`` in the preset (the fixer raises
``E3BrimBumpNotRequested`` otherwise — bumping brim costs filament and
time, so the default is conservative).
"""

from __future__ import annotations

from u1kit.geometry import total_plate_footprint
from u1kit.rules.base import Context, Result, Rule, Severity

BRIM_FIELD = "prime_tower_brim_width"
PRIME_TOWER_ENABLE_FIELD = "prime_tower_enable"
WIPE_TOWER_FILAMENT_FIELD = "wipe_tower_filament"

PLATE_THRESHOLD_MM = 120.0
BRIM_THRESHOLD_MM = 5.0

_TRUE_VALUES = frozenset({"1", "true", "True", "yes", "on"})


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _is_truthy(value: object) -> bool:
    if value is True:
        return True
    if value is False or value is None:
        return False
    return str(value).strip() in _TRUE_VALUES


def _prime_tower_in_use(config: dict[str, object]) -> bool:
    if _is_truthy(config.get(PRIME_TOWER_ENABLE_FIELD)):
        return True
    wipe = config.get(WIPE_TOWER_FILAMENT_FIELD)
    if wipe is None:
        return False
    try:
        return int(str(wipe).strip() or "0") > 0
    except (TypeError, ValueError):
        return False


class E3PrimeTowerBrim(Rule):
    """Warn when prime-tower brim is too thin for the plate footprint."""

    @property
    def id(self) -> str:
        return "E3"

    @property
    def name(self) -> str:
        return "Prime-tower brim width on small plates"

    def check(self, context: Context) -> list[Result]:
        if context.geometry_bounds is None or not context.geometry_bounds:
            return []
        if not _prime_tower_in_use(context.config):
            return []

        width, height = total_plate_footprint(context.geometry_bounds)
        min_dim = min(width, height)
        if min_dim <= 0 or min_dim >= PLATE_THRESHOLD_MM:
            return []

        brim = _parse_float(context.config.get(BRIM_FIELD))
        if brim is None or brim >= BRIM_THRESHOLD_MM:
            return []

        return [
            Result(
                rule_id=self.id,
                severity=Severity.WARN,
                message=(
                    f"Plate footprint ({min_dim:.0f} mm min dim) is small and "
                    f"prime_tower_brim_width is {brim:.2f} mm; the tower may "
                    f"tip over. Bump brim to ≥{BRIM_THRESHOLD_MM:.0f} mm "
                    f"(opt-in via preset option 'e3_auto_bump')."
                ),
                fixer_id="e3",
                diff_preview=None,
            )
        ]
