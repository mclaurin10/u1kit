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
