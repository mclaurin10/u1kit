"""B5: Flexible filaments should not be used as support or support-interface.

Flexibles detach poorly from the part and leave stringy marks at support
contact points. If a non-flexible alternative exists in the filament list,
B5 emits a FAIL with a fixer; otherwise it emits a WARN-only reminder
(the user has to adjust the filament list manually).
"""

from __future__ import annotations

from u1kit.filaments import (
    find_rigid_alternative,
    get_filament_field,
    is_flexible,
    parse_scalar_index,
)
from u1kit.rules.base import Context, Result, Rule, Severity

SUPPORT_SELECTORS: tuple[str, ...] = ("support_filament", "support_interface_filament")


class B5FlexibleSupport(Rule):
    """Flag flex-as-support assignments; fixable only if a rigid alt exists."""

    @property
    def id(self) -> str:
        return "B5"

    @property
    def name(self) -> str:
        return "Flexible filament as support"

    def check(self, context: Context) -> list[Result]:
        config = context.config

        problems: list[tuple[str, int, str]] = []
        for field in SUPPORT_SELECTORS:
            idx = parse_scalar_index(config.get(field))
            if idx is None:
                continue
            ftype = get_filament_field(config, "filament_type", idx)
            if is_flexible(ftype):
                problems.append((field, idx, ftype or "?"))

        if not problems:
            return []

        # Any rigid alternative at all? If so, the fixer can help.
        flex_idx = problems[0][1]
        alt = find_rigid_alternative(config, exclude_index=flex_idx)
        has_fix = alt is not None

        lines = [
            f"{field} -> filament {idx + 1} ({ftype}, flexible)"
            for field, idx, ftype in problems
        ]
        diff = "\n".join(lines)

        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL if has_fix else Severity.WARN,
                message=(
                    "Flexible filament assigned to support role:\n" + diff
                    if has_fix
                    else (
                        "Flexible filament assigned to support, and no "
                        "rigid alternative is present — swap materials "
                        "manually:\n" + diff
                    )
                ),
                fixer_id="b5" if has_fix else None,
                diff_preview=diff,
            )
        ]
