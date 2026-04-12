"""Rule registry."""

from __future__ import annotations

from u1kit.rules.a1_source_slicer import A1SourceSlicer
from u1kit.rules.a2_printer_profile import A2PrinterProfile
from u1kit.rules.a3_bambu_macros import A3BambuMacros
from u1kit.rules.b1_filament_count import B1FilamentCount
from u1kit.rules.b2_filament_mapping import B2FilamentMapping
from u1kit.rules.b3_bbl_fields import B3BblFields
from u1kit.rules.base import Context, Result, Rule, Severity
from u1kit.rules.d1_mixed_height_bounds import D1MixedHeightBounds

__all__ = [
    "RULES",
    "Context",
    "Result",
    "Rule",
    "Severity",
    "get_rule",
]

# Ordered list of all rule classes
RULES: list[type[Rule]] = [
    A1SourceSlicer,
    A2PrinterProfile,
    A3BambuMacros,
    B1FilamentCount,
    B2FilamentMapping,
    B3BblFields,
    D1MixedHeightBounds,
]

_RULE_MAP: dict[str, type[Rule]] = {cls().id: cls for cls in RULES}


def get_rule(rule_id: str) -> type[Rule]:
    """Get a rule class by its ID."""
    if rule_id not in _RULE_MAP:
        raise KeyError(f"Unknown rule ID: {rule_id!r}")
    return _RULE_MAP[rule_id]
