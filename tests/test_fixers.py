"""Tests for fixers — each fixer should produce a clean lint after application."""

from __future__ import annotations

import copy
import io
from typing import Any

from tests.conftest import make_bambu_4color_3mf, make_full_spectrum_3mf
from u1kit.archive import read_3mf
from u1kit.config import parse_config
from u1kit.fixers import get_fixer_map
from u1kit.fixers.base import FixMode, Pipeline
from u1kit.rules import RULES
from u1kit.rules.a2_printer_profile import A2PrinterProfile
from u1kit.rules.a3_bambu_macros import A3BambuMacros
from u1kit.rules.b2_filament_mapping import B2FilamentMapping
from u1kit.rules.b3_bbl_fields import B3BblFields
from u1kit.rules.base import Context, Severity
from u1kit.rules.d1_mixed_height_bounds import D1MixedHeightBounds


class TestA2Fixer:
    """A2 fixer: rewrite printer profile."""

    def test_fixes_bambu_profile(self) -> None:
        config: dict[str, Any] = {
            "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
            "printer_model": "Bambu Lab X1 Carbon",
        }
        pipeline = Pipeline(
            rules=[A2PrinterProfile],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        results, fixer_results, updated, _ = pipeline.run(config, {})

        assert any(fr.applied for fr in fixer_results)
        assert updated["printer_settings_id"] == "Snapmaker U1 (0.4 nozzle)"
        assert updated["printer_model"] == "Snapmaker U1"

    def test_post_fix_passes_lint(self) -> None:
        config: dict[str, Any] = {
            "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
            "printer_model": "Bambu Lab X1 Carbon",
        }
        pipeline = Pipeline(
            rules=[A2PrinterProfile],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {})

        # Re-lint
        ctx = Context(config=updated)
        results = A2PrinterProfile().check(ctx)
        assert len(results) == 0


class TestA3Fixer:
    """A3 fixer: strip Bambu macros."""

    def test_strips_m620(self) -> None:
        config: dict[str, Any] = {
            "machine_start_gcode": "G28\nM620 S0A\nG1 X0\n",
            "machine_end_gcode": "M400\n",
            "change_filament_gcode": (
                "M620 S[next_extruder]A\nT[next_extruder]\nM621 S[next_extruder]A"
            ),
            "layer_change_gcode": ";LAYER_CHANGE\n",
        }
        pipeline = Pipeline(
            rules=[A3BambuMacros],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, fixer_results, updated, _ = pipeline.run(config, {})

        assert any(fr.applied for fr in fixer_results)
        assert "M620" not in updated["machine_start_gcode"]
        assert "M621" not in updated["change_filament_gcode"]

    def test_post_fix_passes_lint(self) -> None:
        config: dict[str, Any] = {
            "machine_start_gcode": "M620 S0A\n",
            "machine_end_gcode": "",
            "change_filament_gcode": "M621 S1A\n",
            "layer_change_gcode": "",
        }
        pipeline = Pipeline(
            rules=[A3BambuMacros],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {})

        ctx = Context(config=updated)
        results = A3BambuMacros().check(ctx)
        assert len(results) == 0


class TestB2Fixer:
    """B2 fixer: auto-assign filament mapping."""

    def test_assigns_mapping(self) -> None:
        config: dict[str, Any] = {
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        }
        pipeline = Pipeline(
            rules=[B2FilamentMapping],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, fixer_results, updated, _ = pipeline.run(config, {})

        assert any(fr.applied for fr in fixer_results)
        assert updated["filament_map"] == [1, 2, 3, 4]

    def test_post_fix_passes_lint(self) -> None:
        config: dict[str, Any] = {
            "filament_colour": "#FF0000;#00FF00",
        }
        pipeline = Pipeline(
            rules=[B2FilamentMapping],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {})

        ctx = Context(config=updated)
        results = B2FilamentMapping().check(ctx)
        assert len(results) == 0


class TestB3Fixer:
    """B3 fixer: remove BBL fields."""

    def test_removes_bbl_fields(self) -> None:
        config: dict[str, Any] = {
            "bbl_use_printhost": "1",
            "bbl_calib_mark_logo": "1",
            "inherits": "Bambu Lab X1 Carbon 0.4 nozzle",
            "compatible_printers": "Bambu Lab X1 Carbon 0.4 nozzle",
        }
        filament_configs: dict[str, dict[str, Any]] = {
            "Metadata/filament_1.config": {
                "filament_extruder_variant": "BBL X1C 0.4",
                "inherits": "Bambu Lab Generic PLA",
            }
        }
        pipeline = Pipeline(
            rules=[B3BblFields],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, fixer_results, updated_config, updated_fils = pipeline.run(
            config, filament_configs
        )

        assert any(fr.applied for fr in fixer_results)
        assert "bbl_use_printhost" not in updated_config
        assert "bbl_calib_mark_logo" not in updated_config
        assert "inherits" not in updated_config
        assert "compatible_printers" not in updated_config

        fil = updated_fils["Metadata/filament_1.config"]
        assert "filament_extruder_variant" not in fil
        assert "inherits" not in fil


class TestD1Fixer:
    """D1 fixer: lock mixed height bounds."""

    def test_locks_to_uniform(self) -> None:
        config: dict[str, Any] = {
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.04",
            "mixed_filament_height_upper_bound": "0.4",
        }
        pipeline = Pipeline(
            rules=[D1MixedHeightBounds],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, fixer_results, updated, _ = pipeline.run(config, {})

        assert any(fr.applied for fr in fixer_results)
        assert updated["layer_height"] == "0.2"
        assert updated["mixed_filament_height_lower_bound"] == "0.2"
        assert updated["mixed_filament_height_upper_bound"] == "0.2"

    def test_custom_uniform_height(self) -> None:
        config: dict[str, Any] = {
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.04",
            "mixed_filament_height_upper_bound": "0.4",
        }
        pipeline = Pipeline(
            rules=[D1MixedHeightBounds],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {}, options={"uniform_height": 0.16})

        assert updated["layer_height"] == "0.16"
        assert updated["mixed_filament_height_lower_bound"] == "0.16"
        assert updated["mixed_filament_height_upper_bound"] == "0.16"

    def test_post_fix_passes_lint(self) -> None:
        config: dict[str, Any] = {
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.04",
            "mixed_filament_height_upper_bound": "0.4",
        }
        pipeline = Pipeline(
            rules=[D1MixedHeightBounds],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {})

        ctx = Context(config=updated)
        results = D1MixedHeightBounds().check(ctx)
        assert len(results) == 0


class TestFullPipeline:
    """End-to-end: Bambu 4-color -> fix -> lint passes."""

    def test_bambu_to_u1_full_pipeline(self) -> None:
        """Bambu 4-color .3mf through full fix pipeline should pass lint."""
        raw = make_bambu_4color_3mf()
        archive = read_3mf(io.BytesIO(raw))
        config = parse_config(archive.config_bytes)

        filament_configs: dict[str, dict[str, Any]] = {}
        for path, data in archive.get_filament_configs().items():
            filament_configs[path] = parse_config(data)

        # Run fix pipeline with all rules
        pipeline = Pipeline(
            rules=RULES,
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, fixer_results, updated_config, updated_fils = pipeline.run(
            config, filament_configs
        )

        # Verify fixers ran
        applied = [fr for fr in fixer_results if fr.applied]
        assert len(applied) > 0

        # Re-lint should have no failures (except B1 if >4 filaments, which is report-only)
        ctx = Context(config=updated_config, filament_configs=updated_fils)
        all_results = []
        for rule_cls in RULES:
            rule = rule_cls()
            all_results.extend(rule.check(ctx))

        failures = [
            r for r in all_results
            if r.severity == Severity.FAIL and r.fixer_id is not None
        ]
        assert len(failures) == 0, f"Remaining fixable failures: {failures}"

    def test_full_spectrum_d1_fix(self) -> None:
        """Full Spectrum file with bad bounds -> D1 locks all to 0.2."""
        raw = make_full_spectrum_3mf(lower_bound="0.04", layer_height="0.2")
        archive = read_3mf(io.BytesIO(raw))
        config = parse_config(archive.config_bytes)

        pipeline = Pipeline(
            rules=[D1MixedHeightBounds],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        _, _, updated, _ = pipeline.run(config, {})

        assert updated["layer_height"] == "0.2"
        assert updated["mixed_filament_height_lower_bound"] == "0.2"
        assert updated["mixed_filament_height_upper_bound"] == "0.2"


class TestFixerIdempotency:
    """Applying a fixer twice should produce the same state as applying once."""

    def test_a2_idempotent(self) -> None:
        from u1kit.fixers.a2_printer_profile import A2PrinterProfileFixer

        config: dict[str, Any] = {
            "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
            "printer_model": "Bambu Lab X1 Carbon",
        }
        fixer = A2PrinterProfileFixer()
        ctx = Context(config=config)
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot

    def test_a3_idempotent(self) -> None:
        from u1kit.fixers.a3_bambu_macros import A3BambuMacrosFixer

        config: dict[str, Any] = {
            "machine_start_gcode": "G28\nM620 S0A\nG1 X0\n",
            "machine_end_gcode": "M400\n",
            "change_filament_gcode": "M620 S[next_extruder]A\nT1\nM621 S1A\n",
            "layer_change_gcode": ";LAYER_CHANGE\n",
        }
        fixer = A3BambuMacrosFixer()
        ctx = Context(config=config)
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot

    def test_b2_idempotent(self) -> None:
        from u1kit.fixers.b2_filament_mapping import B2FilamentMappingFixer

        config: dict[str, Any] = {
            "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        }
        fixer = B2FilamentMappingFixer()
        ctx = Context(config=config)
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot

    def test_b3_idempotent(self) -> None:
        from u1kit.fixers.b3_bbl_fields import B3BblFieldsFixer

        config: dict[str, Any] = {
            "bbl_use_printhost": "1",
            "bbl_calib_mark_logo": "1",
            "inherits": "Bambu Lab X1 Carbon 0.4 nozzle",
            "compatible_printers": "Bambu Lab X1 Carbon 0.4 nozzle",
        }
        filament_configs: dict[str, dict[str, Any]] = {
            "Metadata/filament_1.config": {
                "filament_extruder_variant": "BBL X1C 0.4",
                "inherits": "Bambu Lab Generic PLA",
            }
        }
        fixer = B3BblFieldsFixer()
        ctx = Context(config=config, filament_configs=filament_configs)
        fixer.apply(config, filament_configs, ctx)
        snap_config = copy.deepcopy(config)
        snap_fils = copy.deepcopy(filament_configs)
        fixer.apply(config, filament_configs, ctx)
        assert config == snap_config
        assert filament_configs == snap_fils

    def test_d1_idempotent(self) -> None:
        from u1kit.fixers.d1_mixed_height_bounds import D1MixedHeightBoundsFixer

        config: dict[str, Any] = {
            "layer_height": "0.2",
            "mixed_filament_height_lower_bound": "0.04",
            "mixed_filament_height_upper_bound": "0.4",
        }
        fixer = D1MixedHeightBoundsFixer()
        ctx = Context(config=config, options={"uniform_height": 0.2})
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot

    def test_b4_idempotent(self) -> None:
        from u1kit.fixers.b4_flexible_speed_caps import B4FlexibleSpeedCapsFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "20"],
            "layer_height": "0.2",
            "outer_wall_line_width": "0.42",
            "outer_wall_speed": "60",
            "wall_filament": "2",
        }
        fixer = B4FlexibleSpeedCapsFixer()
        ctx = Context(config=config)
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot

    def test_b5_idempotent(self) -> None:
        from u1kit.fixers.b5_flexible_support import B5FlexibleSupportFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "2",
            "support_interface_filament": "2",
        }
        fixer = B5FlexibleSupportFixer()
        ctx = Context(config=config)
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot


class TestB4Fixer:
    """B4 fixer: cap flexible filaments' volumetric speed and derive wall caps."""

    def test_caps_max_volumetric_speed(self) -> None:
        from u1kit.fixers.b4_flexible_speed_caps import B4FlexibleSpeedCapsFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "20"],
            "layer_height": "0.2",
            "outer_wall_line_width": "0.42",
            "outer_wall_speed": "60",
            "wall_filament": "2",
        }
        B4FlexibleSpeedCapsFixer().apply(config, {}, Context(config=config))
        assert config["filament_max_volumetric_speed"][0] == "20"  # PLA unchanged
        assert float(config["filament_max_volumetric_speed"][1]) <= 5.0

    def test_broadcasts_outer_wall_speed_to_list(self) -> None:
        from u1kit.fixers.b4_flexible_speed_caps import B4FlexibleSpeedCapsFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "20"],
            "layer_height": "0.2",
            "outer_wall_line_width": "0.42",
            "outer_wall_speed": "60",
            "wall_filament": "2",
        }
        B4FlexibleSpeedCapsFixer().apply(config, {}, Context(config=config))
        outer = config["outer_wall_speed"]
        assert isinstance(outer, list)
        assert len(outer) == 2
        assert outer[0] == "60"  # PLA slot preserved
        # 5 / (0.42 * 0.2) * 0.8 ≈ 47.6 mm/s
        assert 40.0 <= float(outer[1]) <= 55.0

    def test_non_flex_slots_unchanged(self) -> None:
        from u1kit.fixers.b4_flexible_speed_caps import B4FlexibleSpeedCapsFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "PETG"],
            "filament_colour": ["#000", "#111"],
            "filament_max_volumetric_speed": ["20", "15"],
            "outer_wall_speed": "60",
        }
        B4FlexibleSpeedCapsFixer().apply(config, {}, Context(config=config))
        assert config["filament_max_volumetric_speed"] == ["20", "15"]

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.b4_flexible_speed_caps import B4FlexibleSpeedCapsFixer
        from u1kit.rules.b4_flexible_speed_caps import B4FlexibleSpeedCaps

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "outer_wall_line_width": "0.42",
            "outer_wall_speed": "60",
            "wall_filament": "2",
        }
        B4FlexibleSpeedCapsFixer().apply(config, {}, Context(config=config))
        results = B4FlexibleSpeedCaps().check(Context(config=config))
        assert len(results) == 0


class TestB5Fixer:
    """B5 fixer: swap flexible support for a rigid alternative."""

    def test_reassigns_support_to_pla(self) -> None:
        from u1kit.fixers.b5_flexible_support import B5FlexibleSupportFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "2",
            "support_interface_filament": "2",
        }
        B5FlexibleSupportFixer().apply(config, {}, Context(config=config))
        assert config["support_filament"] == "1"
        assert config["support_interface_filament"] == "1"

    def test_only_interface_needs_swap(self) -> None:
        from u1kit.fixers.b5_flexible_support import B5FlexibleSupportFixer

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "1",
            "support_interface_filament": "2",
        }
        B5FlexibleSupportFixer().apply(config, {}, Context(config=config))
        assert config["support_filament"] == "1"
        assert config["support_interface_filament"] == "1"

    def test_no_rigid_alt_is_noop(self) -> None:
        from u1kit.fixers.b5_flexible_support import B5FlexibleSupportFixer

        config: dict[str, Any] = {
            "filament_type": ["TPU", "PEBA"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "1",
            "support_interface_filament": "1",
        }
        snapshot = copy.deepcopy(config)
        B5FlexibleSupportFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.b5_flexible_support import B5FlexibleSupportFixer
        from u1kit.rules.b5_flexible_support import B5FlexibleSupport

        config: dict[str, Any] = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#000", "#111"],
            "support_filament": "2",
            "support_interface_filament": "2",
        }
        B5FlexibleSupportFixer().apply(config, {}, Context(config=config))
        results = B5FlexibleSupport().check(Context(config=config))
        assert len(results) == 0


class TestC1Fixer:
    """C1 fixer: normalize conflicting bed-temp fields to min across used slots."""

    def test_sets_used_slots_to_min(self) -> None:
        from u1kit.fixers.c1_bed_temp_conflict import C1BedTempConflictFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        assert config["hot_plate_temp"] == ["50", "50"]

    def test_leaves_unused_slot_alone(self) -> None:
        from u1kit.fixers.c1_bed_temp_conflict import C1BedTempConflictFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111", "#222"],
            "hot_plate_temp": ["50", "60", "100"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        assert config["hot_plate_temp"][0] == "50"
        assert config["hot_plate_temp"][1] == "50"
        assert config["hot_plate_temp"][2] == "100"

    def test_multiple_fields_normalized(self) -> None:
        from u1kit.fixers.c1_bed_temp_conflict import C1BedTempConflictFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "textured_plate_temp": ["55", "65"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        assert config["hot_plate_temp"] == ["50", "50"]
        assert config["textured_plate_temp"] == ["55", "55"]

    def test_idempotent(self) -> None:
        from u1kit.fixers.c1_bed_temp_conflict import C1BedTempConflictFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        snapshot = copy.deepcopy(config)
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.c1_bed_temp_conflict import C1BedTempConflictFixer
        from u1kit.rules.c1_bed_temp_conflict import C1BedTempConflict

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp": ["50", "60"],
            "textured_plate_temp": ["55", "65"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C1BedTempConflictFixer().apply(config, {}, Context(config=config))
        results = C1BedTempConflict().check(Context(config=config))
        assert len(results) == 0


class TestC2Fixer:
    """C2 fixer: normalize first-layer bed-temp + 65C cap on textured."""

    def test_sets_used_slots_to_min(self) -> None:
        from u1kit.fixers.c2_first_layer_bed_temp import C2FirstLayerBedTempFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "60"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        assert config["hot_plate_temp_initial_layer"] == ["50", "50"]

    def test_textured_capped_at_65(self) -> None:
        from u1kit.fixers.c2_first_layer_bed_temp import C2FirstLayerBedTempFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "textured_plate_temp_initial_layer": ["70", "70"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        assert config["textured_plate_temp_initial_layer"] == ["65", "65"]

    def test_hot_initial_not_capped_at_65(self) -> None:
        from u1kit.fixers.c2_first_layer_bed_temp import C2FirstLayerBedTempFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["70", "70"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        snapshot = copy.deepcopy(config)
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_idempotent(self) -> None:
        from u1kit.fixers.c2_first_layer_bed_temp import C2FirstLayerBedTempFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "60"],
            "textured_plate_temp_initial_layer": ["70", "75"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        snapshot = copy.deepcopy(config)
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.c2_first_layer_bed_temp import C2FirstLayerBedTempFixer
        from u1kit.rules.c2_first_layer_bed_temp import C2FirstLayerBedTemp

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "hot_plate_temp_initial_layer": ["50", "60"],
            "textured_plate_temp_initial_layer": ["70", "75"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C2FirstLayerBedTempFixer().apply(config, {}, Context(config=config))
        results = C2FirstLayerBedTemp().check(Context(config=config))
        assert len(results) == 0


class TestC3Fixer:
    """C3 fixer: set used slow_down_layer_time to max() across used slots."""

    def test_sets_used_slots_to_max(self) -> None:
        from u1kit.fixers.c3_slow_down_layer_time import C3SlowDownLayerTimeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C3SlowDownLayerTimeFixer().apply(config, {}, Context(config=config))
        assert config["slow_down_layer_time"] == ["12", "12"]

    def test_unused_slot_preserved(self) -> None:
        from u1kit.fixers.c3_slow_down_layer_time import C3SlowDownLayerTimeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111", "#222"],
            "slow_down_layer_time": ["4", "12", "30"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C3SlowDownLayerTimeFixer().apply(config, {}, Context(config=config))
        assert config["slow_down_layer_time"][0] == "12"
        assert config["slow_down_layer_time"][1] == "12"
        assert config["slow_down_layer_time"][2] == "30"

    def test_idempotent(self) -> None:
        from u1kit.fixers.c3_slow_down_layer_time import C3SlowDownLayerTimeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C3SlowDownLayerTimeFixer().apply(config, {}, Context(config=config))
        snapshot = copy.deepcopy(config)
        C3SlowDownLayerTimeFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.c3_slow_down_layer_time import C3SlowDownLayerTimeFixer
        from u1kit.rules.c3_slow_down_layer_time import C3SlowDownLayerTime

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "slow_down_layer_time": ["4", "12"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        C3SlowDownLayerTimeFixer().apply(config, {}, Context(config=config))
        results = C3SlowDownLayerTime().check(Context(config=config))
        assert len(results) == 0


class TestD2Fixer:
    """D2 fixer: cap z_hop to min(1.5, 4*layer_height), zero filament_z_hop."""

    def test_caps_z_hop(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["2.0", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        # target = min(1.5, 4*0.2) = 0.8
        assert config["z_hop"][0] == "0.8"
        assert config["z_hop"][1] == "0.5"
        assert config["filament_z_hop"][0] == "0"

    def test_zeros_filament_z_hop_when_only_that_field_trips(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["0.5", "0.5"],
            "filament_z_hop": ["2.0", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        # z_hop[0] was below trigger, so not capped
        assert config["z_hop"][0] == "0.5"
        # filament_z_hop[0] always zeroed when the slot trips
        assert config["filament_z_hop"][0] == "0"
        assert config["filament_z_hop"][1] == "0.5"

    def test_unused_slot_preserved(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111", "#222"],
            "layer_height": "0.2",
            "z_hop": ["2.0", "0.5", "3.0"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        assert config["z_hop"][0] == "0.8"
        assert config["z_hop"][1] == "0.5"
        # slot 2 is unused, preserved even though it trips
        assert config["z_hop"][2] == "3.0"

    def test_no_trip_is_noop(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["0.5", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        before = copy.deepcopy(config)
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        assert config == before

    def test_idempotent(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["2.0", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        snapshot = copy.deepcopy(config)
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_post_fix_passes_lint(self) -> None:
        from u1kit.fixers.d2_z_hop_magnitude import D2ZHopMagnitudeFixer
        from u1kit.rules.d2_z_hop_magnitude import D2ZHopMagnitude

        config: dict[str, Any] = {
            "filament_colour": ["#000", "#111"],
            "layer_height": "0.2",
            "z_hop": ["2.0", "0.5"],
            "filament_z_hop": ["1.8", "0.5"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        D2ZHopMagnitudeFixer().apply(config, {}, Context(config=config))
        results = D2ZHopMagnitude().check(Context(config=config))
        assert len(results) == 0
