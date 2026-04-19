"""D3: info-only notice when 1:1 alternating mixed blends are in use.

A 1:1 (ratio_percent == 50) alternation in ``mixed_filament_definitions``
forces a toolchange on every layer for the blended extrusion, which
multiplies toolchange time across the print. We do not compute exact layer
counts here (that needs the geometry parser from Task 12); we only surface
that such blends exist so the operator can reconsider the blend ratio.
"""

from __future__ import annotations

from u1kit.mixed_blends import parse_mixed_definitions
from u1kit.rules.base import Context, Result, Rule, Severity

MIXED_DEFINITIONS_FIELD = "mixed_filament_definitions"


class D3AlternationCost(Rule):
    """Emit INFO when at least one 1:1 alternating blend is defined."""

    @property
    def id(self) -> str:
        return "D3"

    @property
    def name(self) -> str:
        return "Mixed-blend alternation cost"

    def check(self, context: Context) -> list[Result]:
        raw = context.config.get(MIXED_DEFINITIONS_FIELD)
        if not isinstance(raw, str):
            return []

        blends = parse_mixed_definitions(raw)
        alternating = [b for b in blends if b.ratio_percent == 50]
        if not alternating:
            return []

        count = len(alternating)
        plural = "s" if count != 1 else ""
        slot_pairs = ", ".join(
            f"({b.filament_a},{b.filament_b})" for b in alternating
        )
        diff = (
            f"{count} 1:1 alternating blend{plural}: {slot_pairs} — each layer "
            "forces a toolchange on the blended extrusion."
        )
        return [
            Result(
                rule_id=self.id,
                severity=Severity.INFO,
                message=(
                    "Mixed-blend alternation cost: "
                    f"{count} 1:1 blend{plural} will add a toolchange per "
                    "layer. Consider a non-50/50 ratio if cycle time "
                    "matters:\n" + diff
                ),
                fixer_id=None,
                diff_preview=diff,
            )
        ]
