"""D2: warn when per-filament Z-hop magnitude is >= 5x layer_height.

Full Spectrum's toolchanger can set a per-filament Z-hop that is applied in
addition to the global ``z_hop``. When either field exceeds roughly 5x the
layer height, the head lifts enough that oozing, stringing, and nozzle-wipe
failures become likely on the Snapmaker U1. Both fields are parallel arrays;
this rule checks only the used slots so unused filament templates do not
generate spurious warnings.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

Z_HOP_FIELD = "z_hop"
FILAMENT_Z_HOP_FIELD = "filament_z_hop"


def _parse_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class D2ZHopMagnitude(Rule):
    """Warn on z-hop >= 5x layer_height among used filaments."""

    @property
    def id(self) -> str:
        return "D2"

    @property
    def name(self) -> str:
        return "Z-hop magnitude"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)
        if not used:
            return []

        layer_height = _parse_float(config.get("layer_height"))
        if layer_height is None or layer_height <= 0:
            return []

        trigger = 5 * layer_height
        offenders: list[str] = []
        for i in used:
            z = _parse_float(get_filament_field(config, Z_HOP_FIELD, i)) or 0.0
            fz = _parse_float(
                get_filament_field(config, FILAMENT_Z_HOP_FIELD, i)
            ) or 0.0
            high = max(z, fz)
            if high >= trigger:
                offenders.append(
                    f"slot {i}: max(z_hop={z:g}, filament_z_hop={fz:g}) = "
                    f"{high:g} >= {trigger:g}"
                )

        if not offenders:
            return []

        diff = "\n".join(offenders)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.WARN,
                message=(
                    "Z-hop magnitude exceeds 5x layer_height on used "
                    "filaments — stringing and wipe failures likely:\n" + diff
                ),
                fixer_id="d2",
                diff_preview=diff,
            )
        ]
