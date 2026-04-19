"""Tests for all rules — positive and negative cases."""

from __future__ import annotations

from u1kit.rules.a1_source_slicer import A1SourceSlicer
from u1kit.rules.a2_printer_profile import A2PrinterProfile
from u1kit.rules.a3_bambu_macros import A3BambuMacros
from u1kit.rules.b1_filament_count import B1FilamentCount
from u1kit.rules.b2_filament_mapping import B2FilamentMapping
from u1kit.rules.b3_bbl_fields import B3BblFields
from u1kit.rules.b4_flexible_speed_caps import B4FlexibleSpeedCaps
from u1kit.rules.b5_flexible_support import B5FlexibleSupport
from u1kit.rules.base import Context, Severity
from u1kit.rules.c1_bed_temp_conflict import C1BedTempConflict
from u1kit.rules.c2_first_layer_bed_temp import C2FirstLayerBedTemp
from u1kit.rules.c3_slow_down_layer_time import C3SlowDownLayerTime
from u1kit.rules.c4_fan_speed_range import C4FanSpeedRange
from u1kit.rules.d1_mixed_height_bounds import D1MixedHeightBounds
from u1kit.rules.d2_z_hop_magnitude import D2ZHopMagnitude
from u1kit.rules.d3_alternation_cost import D3AlternationCost
from u1kit.rules.e1_thin_feature import E1ThinFeature


class TestA1SourceSlicer:
    """A1: detect source slicer."""

    def test_detects_bambu(self) -> None:
        ctx = Context(config={
            "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
            "printer_model": "Bambu Lab X1 Carbon",
        })
        results = A1SourceSlicer().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO
        assert ctx.source_slicer == "bambu"

    def test_detects_full_spectrum(self) -> None:
        ctx = Context(config={
            "mixed_filament_height_lower_bound": "0.1",
            "printer_settings_id": "Snapmaker U1",
        })
        results = A1SourceSlicer().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO
        assert ctx.source_slicer == "full_spectrum"

    def test_unknown_slicer(self) -> None:
        ctx = Context(config={"printer_settings_id": "SomeOtherSlicer"})
        results = A1SourceSlicer().check(ctx)
        assert len(results) == 1
        assert ctx.source_slicer == "unknown"


class TestA2PrinterProfile:
    """A2: printer profile must be U1."""

    def test_bambu_profile_fails(self) -> None:
        ctx = Context(config={
            "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
            "printer_model": "Bambu Lab X1 Carbon",
        })
        results = A2PrinterProfile().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "a2"

    def test_u1_profile_passes(self) -> None:
        ctx = Context(config={
            "printer_settings_id": "Snapmaker U1 (0.4 nozzle)",
            "printer_model": "Snapmaker U1",
        })
        results = A2PrinterProfile().check(ctx)
        assert len(results) == 0


class TestA3BambuMacros:
    """A3: detect Bambu AMS macros."""

    def test_m620_detected(self) -> None:
        ctx = Context(config={
            "machine_start_gcode": "G28\nM620 S0A\nG1 X0\n",
            "change_filament_gcode": "",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "a3"

    def test_m621_detected(self) -> None:
        ctx = Context(config={
            "change_filament_gcode": "M621 S1A\nT1\n",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL

    def test_m623_detected(self) -> None:
        ctx = Context(config={
            "machine_start_gcode": "G28\nM623\nG1 X0\n",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "a3"

    def test_ams_keyword_detected(self) -> None:
        ctx = Context(config={
            "change_filament_gcode": "; AMS filament change\nT1\n",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL

    def test_multiple_fields_single_result(self) -> None:
        ctx = Context(config={
            "machine_start_gcode": "G28\nM620 S0A\n",
            "change_filament_gcode": "M621 S1A\nT1\n",
            "machine_end_gcode": "",
            "layer_change_gcode": "",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 1
        assert results[0].diff_preview is not None
        assert "machine_start_gcode" in results[0].diff_preview
        assert "change_filament_gcode" in results[0].diff_preview

    def test_clean_gcode_passes(self) -> None:
        ctx = Context(config={
            "machine_start_gcode": "G28\nG1 X0 Y0\n",
            "machine_end_gcode": "M400\nM104 S0\n",
            "change_filament_gcode": "T[next_extruder]\n",
            "layer_change_gcode": ";LAYER_CHANGE\n",
        })
        results = A3BambuMacros().check(ctx)
        assert len(results) == 0


class TestB1FilamentCount:
    """B1: filament count <= 4."""

    def test_4_filaments_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        })
        results = B1FilamentCount().check(ctx)
        assert len(results) == 0

    def test_5_filaments_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00;#FF00FF",
        })
        results = B1FilamentCount().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "b1"

    def test_empty_passes(self) -> None:
        ctx = Context(config={"filament_colour": ""})
        results = B1FilamentCount().check(ctx)
        assert len(results) == 0


class TestB2FilamentMapping:
    """B2: filament-to-extruder mapping."""

    def test_missing_mapping_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        })
        results = B2FilamentMapping().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "b2"

    def test_valid_mapping_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
            "filament_map": [1, 2, 3, 4],
        })
        results = B2FilamentMapping().check(ctx)
        assert len(results) == 0

    def test_invalid_index_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": "#FF0000;#00FF00",
            "filament_map": [1, 5],
        })
        results = B2FilamentMapping().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL


class TestB3BblFields:
    """B3: Bambu-specific fields."""

    def test_bbl_fields_detected(self) -> None:
        ctx = Context(config={
            "bbl_use_printhost": "1",
            "compatible_printers": "Bambu Lab X1 Carbon",
        })
        results = B3BblFields().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id == "b3"

    def test_clean_config_passes(self) -> None:
        ctx = Context(config={
            "printer_settings_id": "Snapmaker U1",
        })
        results = B3BblFields().check(ctx)
        assert len(results) == 0

    def test_filament_level_bbl_fields(self) -> None:
        ctx = Context(
            config={},
            filament_configs={
                "Metadata/filament_1.config": {
                    "filament_extruder_variant": "BBL X1C 0.4",
                    "inherits": "Bambu Lab Generic PLA",
                }
            },
        )
        results = B3BblFields().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN


class TestD1MixedHeightBounds:
    """D1: mixed height bounds >= layer height."""

    def test_lower_bound_below_layer_height_fails(self) -> None:
        ctx = Context(config={
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.04",
            "mixed_filament_height_upper_bound": "0.4",
        })
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "d1"

    def test_valid_bounds_passes(self) -> None:
        ctx = Context(config={
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.2",
            "mixed_filament_height_upper_bound": "0.4",
        })
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 0

    def test_no_mixed_height_keys_passes(self) -> None:
        """Files without mixed height keys should pass (not applicable)."""
        ctx = Context(config={"layer_height": "0.2"})
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 0

    def test_malformed_lower_bound_reports_fail(self) -> None:
        ctx = Context(config={
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "not-a-number",
        })
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert "not a valid number" in results[0].message
        assert results[0].fixer_id == "d1"

    def test_custom_uniform_height(self) -> None:
        ctx = Context(
            config={
                "layer_height": "0.2",
                "mixed_filament_height_lower_bound": "0.04",
                "mixed_filament_height_upper_bound": "0.4",
            },
            options={"uniform_height": 0.16},
        )
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 1
        assert "0.16" in results[0].message


class TestB4FlexibleSpeedCaps:
    """B4: flexible filaments need a volumetric speed cap."""

    def test_tpu_without_cap_warns(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "wall_filament": "2",
        })
        results = B4FlexibleSpeedCaps().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id == "b4"

    def test_tpu_with_adequate_cap_passes(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "5"],
            "wall_filament": "2",
        })
        results = B4FlexibleSpeedCaps().check(ctx)
        assert len(results) == 0

    def test_tpu_with_too_high_cap_warns(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "20"],
            "wall_filament": "2",
        })
        results = B4FlexibleSpeedCaps().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN

    def test_all_rigid_passes(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "PETG"],
            "filament_colour": ["#000", "#111"],
        })
        results = B4FlexibleSpeedCaps().check(ctx)
        assert len(results) == 0

    def test_unused_flex_is_ignored(self) -> None:
        # TPU present in slot 2 but no selector references it.
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = B4FlexibleSpeedCaps().check(ctx)
        assert len(results) == 0

    def test_empty_config_passes(self) -> None:
        results = B4FlexibleSpeedCaps().check(Context(config={}))
        assert len(results) == 0


class TestB5FlexibleSupport:
    """B5: flexible filaments shouldn't be used as support."""

    def test_flexible_support_with_rigid_alt_fails(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "2",
            "support_interface_filament": "2",
        })
        results = B5FlexibleSupport().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "b5"

    def test_flexible_support_no_rigid_alt_warns(self) -> None:
        ctx = Context(config={
            "filament_type": ["TPU", "PEBA"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "1",
            "support_interface_filament": "1",
        })
        results = B5FlexibleSupport().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id is None

    def test_rigid_support_passes(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "1",
            "support_interface_filament": "1",
        })
        results = B5FlexibleSupport().check(ctx)
        assert len(results) == 0

    def test_no_support_selector_passes(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
        })
        results = B5FlexibleSupport().check(ctx)
        assert len(results) == 0

    def test_interface_only_flexible(self) -> None:
        ctx = Context(config={
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "1",
            "support_interface_filament": "2",
        })
        results = B5FlexibleSupport().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "b5"


class TestC1BedTempConflict:
    """C1: bed-temperature conflict across used filaments."""

    def test_no_bed_temp_fields_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 0

    def test_uniform_bed_temp_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "50"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 0

    def test_conflicting_hot_plate_temp_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "c1"
        assert "hot_plate_temp" in results[0].message

    def test_unused_slots_ignored(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 0

    def test_multiple_plate_fields_summarized(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "textured_plate_temp": ["55", "65"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 1
        assert "hot_plate_temp" in results[0].message
        assert "textured_plate_temp" in results[0].message

    def test_single_used_slot_never_conflicts(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "wall_filament": "1",
        })
        results = C1BedTempConflict().check(ctx)
        assert len(results) == 0


class TestC2FirstLayerBedTemp:
    """C2: first-layer bed-temperature conflict + textured-PEI 65C cap."""

    def test_no_first_layer_fields_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 0

    def test_uniform_first_layer_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "50"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 0

    def test_conflicting_first_layer_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "c2"

    def test_textured_over_65_cap_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "textured_plate_temp_initial_layer": ["70", "70"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "c2"

    def test_textured_at_65_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "textured_plate_temp_initial_layer": ["65", "65"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 0

    def test_hot_plate_initial_over_65_is_not_capped(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["70", "70"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 0

    def test_empty_config_passes(self) -> None:
        results = C2FirstLayerBedTemp().check(Context(config={}))
        assert len(results) == 0

    def test_unused_slots_ignored(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "70"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = C2FirstLayerBedTemp().check(ctx)
        assert len(results) == 0


class TestC3SlowDownLayerTime:
    """C3: cooling-time conflict — pick the max across used filaments."""

    def test_uniform_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "4"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C3SlowDownLayerTime().check(ctx)
        assert len(results) == 0

    def test_conflicting_fails(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C3SlowDownLayerTime().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.FAIL
        assert results[0].fixer_id == "c3"

    def test_unused_slot_ignored(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = C3SlowDownLayerTime().check(ctx)
        assert len(results) == 0

    def test_missing_field_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C3SlowDownLayerTime().check(ctx)
        assert len(results) == 0

    def test_single_used_slot_never_conflicts(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
        })
        results = C3SlowDownLayerTime().check(ctx)
        assert len(results) == 0


class TestC4FanSpeedRange:
    """C4: info-only report of differing fan ranges across used filaments."""

    def test_uniform_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "fan_max_speed": ["100", "100"],
            "fan_min_speed": ["20", "20"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C4FanSpeedRange().check(ctx)
        assert len(results) == 0

    def test_differing_max_emits_info(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "fan_max_speed": ["100", "50"],
            "fan_min_speed": ["20", "20"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C4FanSpeedRange().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO
        assert results[0].fixer_id is None
        assert "fan_max_speed" in results[0].message

    def test_differing_min_emits_info(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "fan_max_speed": ["100", "100"],
            "fan_min_speed": ["20", "0"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = C4FanSpeedRange().check(ctx)
        assert len(results) == 1
        assert "fan_min_speed" in results[0].message

    def test_unused_slots_ignored(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "fan_max_speed": ["100", "50"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = C4FanSpeedRange().check(ctx)
        assert len(results) == 0

    def test_missing_fields_passes(self) -> None:
        results = C4FanSpeedRange().check(Context(config={}))
        assert len(results) == 0


class TestD2ZHopMagnitude:
    """D2: warn when z-hop magnitude is >= 5x layer_height on any used slot."""

    def test_no_z_hop_fields_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 0

    def test_z_hop_below_trigger_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["0.5", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 0

    def test_z_hop_at_trigger_warns(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["1.0", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id == "d2"

    def test_filament_z_hop_trips_trigger(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "filament_z_hop": ["1.0", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN

    def test_max_of_both_fields(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["0.5", "0.5"],
            "filament_z_hop": ["1.2", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 1

    def test_unused_slot_ignored(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["0.5", "2.0"],
            "wall_filament": "1",
            "sparse_infill_filament": "1",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 0

    def test_missing_layer_height_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "z_hop": ["2.0", "2.0"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 0

    def test_empty_string_values_treated_as_zero(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["", ""],
            "filament_z_hop": ["", ""],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D2ZHopMagnitude().check(ctx)
        assert len(results) == 0


class TestD3AlternationCost:
    """D3: info-only notice when >=1 1:1 alternating blend exists."""

    def test_no_mixed_definitions_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        })
        results = D3AlternationCost().check(ctx)
        assert len(results) == 0

    def test_empty_mixed_definitions_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "mixed_filament_definitions": "",
        })
        results = D3AlternationCost().check(ctx)
        assert len(results) == 0

    def test_50_50_blend_emits_info(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "mixed_filament_definitions": "1,2,0,1,50,0,5,0,0,0,0,0",
        })
        results = D3AlternationCost().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.INFO
        assert results[0].fixer_id is None

    def test_non_50_blend_passes(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "mixed_filament_definitions": "1,2,0,1,33,0,5,0,0,0,0,0",
        })
        results = D3AlternationCost().check(ctx)
        assert len(results) == 0

    def test_multiple_blends_only_counts_50(self) -> None:
        ctx = Context(config={
            "filament_colour": ["#000", "#111"],
            "mixed_filament_definitions": (
                "1,2,0,1,50,0,5,0,0,0,0,0;"
                "1,3,0,1,33,0,5,0,0,0,0,0;"
                "1,4,0,1,50,0,5,0,0,0,0,0"
            ),
        })
        results = D3AlternationCost().check(ctx)
        assert len(results) == 1
        assert "2" in results[0].message


class TestE1ThinFeature:
    """E1: warn when any object's thinnest XY < 3x outer_wall_line_width."""

    def test_no_geometry_passes(self) -> None:
        ctx = Context(config={"outer_wall_line_width": "0.4"})
        assert E1ThinFeature().check(ctx) == []

    def test_missing_line_width_passes(self) -> None:
        from u1kit.geometry import ObjectBounds

        ctx = Context(
            config={},
            geometry_bounds=[
                ObjectBounds(
                    id="1",
                    min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=1.0, max_y=1.0, max_z=1.0,
                ),
            ],
        )
        assert E1ThinFeature().check(ctx) == []

    def test_thick_object_passes(self) -> None:
        from u1kit.geometry import ObjectBounds

        ctx = Context(
            config={"outer_wall_line_width": "0.4"},
            geometry_bounds=[
                ObjectBounds(
                    id="1",
                    min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=100.0, max_y=100.0, max_z=50.0,
                ),
            ],
        )
        assert E1ThinFeature().check(ctx) == []

    def test_thin_object_warns(self) -> None:
        from u1kit.geometry import ObjectBounds

        # thinnest_xy = 1.0, line_width = 0.4 → ratio 2.5 < 3 → WARN
        ctx = Context(
            config={"outer_wall_line_width": "0.4"},
            geometry_bounds=[
                ObjectBounds(
                    id="7",
                    min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=100.0, max_y=1.0, max_z=50.0,
                ),
            ],
        )
        results = E1ThinFeature().check(ctx)
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id is None
        assert "7" in results[0].message

    def test_ratio_of_three_is_boundary_pass(self) -> None:
        from u1kit.geometry import ObjectBounds

        # thinnest_xy = 1.5, line_width = 0.5 → ratio 3.0 → not < 3 → pass
        ctx = Context(
            config={"outer_wall_line_width": "0.5"},
            geometry_bounds=[
                ObjectBounds(
                    id="1",
                    min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=100.0, max_y=1.5, max_z=50.0,
                ),
            ],
        )
        assert E1ThinFeature().check(ctx) == []

    def test_multiple_objects_flags_only_thin_ones(self) -> None:
        from u1kit.geometry import ObjectBounds

        ctx = Context(
            config={"outer_wall_line_width": "0.4"},
            geometry_bounds=[
                ObjectBounds(
                    id="thick", min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=100.0, max_y=100.0, max_z=10.0,
                ),
                ObjectBounds(
                    id="thin", min_x=0.0, min_y=0.0, min_z=0.0,
                    max_x=100.0, max_y=0.5, max_z=10.0,
                ),
            ],
        )
        results = E1ThinFeature().check(ctx)
        assert len(results) == 1
        assert "thin" in results[0].message
        assert "thick" not in results[0].message
