"""Tests for all rules — positive and negative cases."""

from __future__ import annotations

from u1kit.rules.a1_source_slicer import A1SourceSlicer
from u1kit.rules.a2_printer_profile import A2PrinterProfile
from u1kit.rules.a3_bambu_macros import A3BambuMacros
from u1kit.rules.b1_filament_count import B1FilamentCount
from u1kit.rules.b2_filament_mapping import B2FilamentMapping
from u1kit.rules.b3_bbl_fields import B3BblFields
from u1kit.rules.base import Context, Severity
from u1kit.rules.d1_mixed_height_bounds import D1MixedHeightBounds


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
