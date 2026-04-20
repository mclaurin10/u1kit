"""Rule registry."""

from __future__ import annotations

from u1kit.rules.a1_source_slicer import A1SourceSlicer
from u1kit.rules.a2_printer_profile import A2PrinterProfile
from u1kit.rules.a3_bambu_macros import A3BambuMacros
from u1kit.rules.b1_filament_count import B1FilamentCount
from u1kit.rules.b2_filament_mapping import B2FilamentMapping
from u1kit.rules.b3_bbl_fields import B3BblFields
from u1kit.rules.b4_flexible_speed_caps import B4FlexibleSpeedCaps
from u1kit.rules.b5_flexible_support import B5FlexibleSupport
from u1kit.rules.base import Context, Result, Rule, Severity
from u1kit.rules.c1_bed_temp_conflict import C1BedTempConflict
from u1kit.rules.c2_first_layer_bed_temp import C2FirstLayerBedTemp
from u1kit.rules.c3_slow_down_layer_time import C3SlowDownLayerTime
from u1kit.rules.c4_fan_speed_range import C4FanSpeedRange
from u1kit.rules.d1_mixed_height_bounds import D1MixedHeightBounds
from u1kit.rules.d2_z_hop_magnitude import D2ZHopMagnitude
from u1kit.rules.d3_alternation_cost import D3AlternationCost
from u1kit.rules.e1_thin_feature import E1ThinFeature
from u1kit.rules.e2_layer_time_clamp import E2LayerTimeClamp
from u1kit.rules.e3_prime_tower_brim import E3PrimeTowerBrim

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
    B4FlexibleSpeedCaps,
    B5FlexibleSupport,
    C1BedTempConflict,
    C2FirstLayerBedTemp,
    C3SlowDownLayerTime,
    C4FanSpeedRange,
    D2ZHopMagnitude,
    D3AlternationCost,
    D1MixedHeightBounds,
    E1ThinFeature,
    E2LayerTimeClamp,
    E3PrimeTowerBrim,
]

_RULE_MAP: dict[str, type[Rule]] = {cls().id: cls for cls in RULES}


def get_rule(rule_id: str) -> type[Rule]:
    """Get a rule class by its ID."""
    if rule_id not in _RULE_MAP:
        raise KeyError(f"Unknown rule ID: {rule_id!r}")
    return _RULE_MAP[rule_id]
