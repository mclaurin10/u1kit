"""C4: surface per-filament fan-speed range differences (info only).

When used filaments disagree on ``fan_max_speed`` or ``fan_min_speed``, there
is no single clamp that preserves each profile's cooling strategy — PETG may
need a lower max than PLA while TPU may need a non-zero min. C4 emits an info
result so the operator can inspect the per-filament profiles. No auto-fix.
"""

from __future__ import annotations

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

FAN_FIELDS: tuple[str, ...] = ("fan_max_speed", "fan_min_speed")


class C4FanSpeedRange(Rule):
    """Info-only: report differing fan ranges across used filaments."""

    @property
    def id(self) -> str:
        return "C4"

    @property
    def name(self) -> str:
        return "Fan speed range across filaments"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        used = get_used_filament_indices(config)
        if len(used) < 2:
            return []

        differences: list[str] = []
        for field in FAN_FIELDS:
            if field not in config:
                continue
            values = [get_filament_field(config, field, i) for i in used]
            distinct = {v for v in values if v is not None}
            if len(distinct) >= 2:
                differences.append(
                    f"{field}: used slots have {sorted(distinct)}"
                )

        if not differences:
            return []

        diff = "\n".join(differences)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.INFO,
                message=(
                    "Fan-speed ranges differ across used filaments "
                    "(no single fix — inspect per-filament profiles):\n" + diff
                ),
                fixer_id=None,
                diff_preview=diff,
            )
        ]
