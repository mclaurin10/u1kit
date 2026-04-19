"""C3: cooling-time conflict — pick the max across used filaments.

PEBA-grade cooling times (~12 s) must override PLA defaults (~4 s) when both
are in use; otherwise the slower-cooling filament lays into a layer that has
not had time to solidify. Unlike bed-temp conflicts the resolution is
**max**, not min: the slowest filament dictates the minimum layer time.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

SLOW_DOWN_FIELD = "slow_down_layer_time"


class C3SlowDownLayerTime(Rule):
    """Flag >=2 distinct slow_down_layer_time values among used filaments."""

    @property
    def id(self) -> str:
        return "C3"

    @property
    def name(self) -> str:
        return "Slow-down layer time conflict"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)
        if len(used) < 2:
            return []
        if SLOW_DOWN_FIELD not in config:
            return []

        values = [get_filament_field(config, SLOW_DOWN_FIELD, i) for i in used]
        distinct = {v for v in values if v is not None}
        if len(distinct) < 2:
            return []

        diff = f"{SLOW_DOWN_FIELD}: used slots have {sorted(distinct)} (target max)"
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=(
                    "Slow-down layer time conflict — the slowest-cooling filament "
                    "must dictate minimum layer time:\n" + diff
                ),
                fixer_id="c3",
                diff_preview=diff,
            )
        ]
