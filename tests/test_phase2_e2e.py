"""End-to-end verification of Phase 2's five starter presets.

Each test builds a minimal .3mf that exercises a preset's rules, runs
``u1kit fix --preset <name>``, then re-lints the output and asserts
the targeted-severity findings are gone. This is the Phase 2 exit
check: every starter preset round-trips cleanly.

The tests live alongside ``test_cli.py``'s narrower per-feature tests
and are intentionally redundant with them at the happy-path level —
their job is to catch breakage in the *composition* of a preset's
rules and fixers under real CliRunner invocation, not to exercise
individual code paths.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from click.testing import CliRunner

from tests.conftest import (
    make_3mf,
    make_full_spectrum_3mf,
    make_model_xml,
)
from u1kit.cli import main
from u1kit.rules.base import Severity


def _run_fix(
    input_path: Path, output_path: Path, preset: str, *extra_args: str
) -> str:
    """Invoke ``u1kit fix --preset`` and assert exit 0. Returns CLI output."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["fix", str(input_path), "--preset", preset, "--out", str(output_path), *extra_args],
    )
    assert result.exit_code == 0, f"fix --preset {preset} failed:\n{result.output}"
    return result.output


def _lint_json(path: Path) -> dict[str, Any]:
    """Invoke ``u1kit lint --json`` and return the parsed payload."""
    runner = CliRunner()
    result = runner.invoke(main, ["lint", str(path), "--json"])
    # Exit 0 (clean) or 1 (has fails) are both valid return states; exit 2 is crash.
    assert result.exit_code in (0, 1), f"lint crashed:\n{result.output}"
    return json.loads(result.output)  # type: ignore[no-any-return]


def _read_config(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as zf:
        raw = zf.read("Metadata/project_settings.config").decode("utf-8")
    return json.loads(raw)  # type: ignore[no-any-return]


class TestBambuToU1Preset:
    """bambu-to-u1: rules A2, A3, B1, B2, B3, D1."""

    def test_bambu_file_relints_clean(self, tmp_path: Path) -> None:
        from tests.conftest import make_bambu_4color_3mf

        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        _run_fix(input_path, output_path, "bambu-to-u1")

        payload = _lint_json(output_path)
        assert payload["schema_version"] == "1"
        # No fail-severity findings left from the preset's rule set.
        fails = [r for r in payload["results"] if r["severity"] == Severity.FAIL.value]
        assert fails == [], f"Unexpected FAIL findings: {fails}"


class TestFsUniformPreset:
    """fs-uniform: rules D1 — mixed_filament_height_bounds must be ≥ layer_height."""

    def test_full_spectrum_fix_equalizes_bounds(self, tmp_path: Path) -> None:
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(
            make_full_spectrum_3mf(lower_bound="0.04", layer_height="0.2")
        )

        _run_fix(input_path, output_path, "fs-uniform")

        config = _read_config(output_path)
        assert config["mixed_filament_height_lower_bound"] == "0.2"
        assert config["mixed_filament_height_upper_bound"] == "0.2"


class TestPebaSafePreset:
    """peba-safe: rules D1, D2, B4, B5, C3, E3 — flexible-filament conservative ruleset."""

    def test_flexible_file_fix_reduces_findings(self, tmp_path: Path) -> None:
        # Flexible (TPU) + rigid (PLA). B5 should reroute support to PLA.
        # B4 should inject a speed cap. D2 should cap z_hop.
        config: dict[str, Any] = {
            "printer_settings_id": "Snapmaker U1 (0.4 nozzle)",
            "printer_model": "Snapmaker U1",
            "layer_height": "0.2",
            "filament_colour": ["#FF0000", "#00FF00"],
            "filament_type": ["PLA", "TPU"],
            "filament_settings_id": [
                "Snapmaker PLA @Snapmaker U1",
                "Snapmaker TPU @Snapmaker U1",
            ],
            "filament_max_volumetric_speed": ["25", "25"],  # TPU too fast
            "slow_down_layer_time": ["8", "30"],
            "z_hop": ["2.0", "2.0"],  # way above 4 * layer_height
            "support_filament": "2",  # flexible as support
            "support_interface_filament": "2",
            "wall_filament": "1",
            "sparse_infill_filament": "2",
        }
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_3mf(config=config))

        # B4 prompts for re-lint; use --uniform-height default.
        _run_fix(input_path, output_path, "peba-safe")

        payload = _lint_json(output_path)
        # These preset rules should be silent post-fix at fail/warn severity.
        # (Info-level findings from other rules are OK.)
        preset_rule_ids = {"D1", "D2", "B4", "B5", "C3", "E3"}
        remaining = [
            r
            for r in payload["results"]
            if r["rule_id"] in preset_rule_ids
            and r["severity"] in (Severity.FAIL.value, Severity.WARN.value)
        ]
        assert remaining == [], f"Preset rules still firing: {remaining}"

        updated = _read_config(output_path)
        # B5 should have moved support off slot 2 (flexible).
        assert updated["support_filament"] == "1"


class TestPlusPebaMultiPreset:
    """plus-peba-multi: peba-safe + C1 (bed temp) + C2 (first-layer) + C4 (fan)."""

    def test_multi_flexible_fix_reconciles_bed_temps(self, tmp_path: Path) -> None:
        config: dict[str, Any] = {
            "printer_settings_id": "Snapmaker U1 (0.4 nozzle)",
            "printer_model": "Snapmaker U1",
            "layer_height": "0.2",
            "filament_colour": ["#FF0000", "#00FF00", "#0000FF"],
            "filament_type": ["PLA", "TPU", "PETG"],
            "filament_settings_id": [
                "Snapmaker PLA @Snapmaker U1",
                "Snapmaker TPU @Snapmaker U1",
                "Snapmaker PETG @Snapmaker U1",
            ],
            # Conflicting bed temps across used slots → C1 fires.
            "hot_plate_temp": ["60", "45", "70"],
            "textured_plate_temp": ["55", "45", "70"],
            "filament_max_volumetric_speed": ["25", "25", "25"],
            "slow_down_layer_time": ["8", "30", "10"],
            "z_hop": ["0.2", "0.2", "0.2"],
            "support_filament": "1",
            "support_interface_filament": "1",
            "wall_filament": "1",
            "sparse_infill_filament": "3",
            "wipe_tower_filament": "2",
        }
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_3mf(config=config))

        _run_fix(input_path, output_path, "plus-peba-multi")

        updated = _read_config(output_path)
        # C1 fixer picks the min used; across used indices (0,1,2) → min is 45.
        assert set(updated["hot_plate_temp"]) == {"45"}


class TestMakerworldImportPreset:
    """makerworld-import: rules A2, A3, B1, B2, B3, D1, C1, C2, B4."""

    def test_makerworld_file_produces_u1_profile(self, tmp_path: Path) -> None:
        # Start from a bambu-style config with >4 filaments (triggers B1).
        from tests.conftest import make_bambu_4color_3mf

        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        _run_fix(input_path, output_path, "makerworld-import")

        updated = _read_config(output_path)
        # A2: printer profile rewritten to U1.
        assert "U1" in updated["printer_settings_id"]
        # B3: bbl_use_printhost should be cleared.
        assert "bbl_use_printhost" not in updated or updated["bbl_use_printhost"] in (
            "0",
            "",
        )

        payload = _lint_json(output_path)
        # All preset-targeted fail findings resolved.
        fails = [
            r
            for r in payload["results"]
            if r["severity"] == Severity.FAIL.value
            and r["rule_id"] in {"A2", "A3", "B1", "B2", "B3", "D1", "C1", "C2"}
        ]
        assert fails == [], f"Unresolved FAIL findings: {fails}"


class TestE3OptInViaPreset:
    """peba-safe and plus-peba-multi gate E3's fixer with e3_auto_bump=true."""

    def test_small_plate_e3_fires_under_peba_safe(self, tmp_path: Path) -> None:
        # 80x80 small plate, small brim → E3 rule fires, fixer opts in.
        model_xml = make_model_xml([
            ("1", [
                (0.0, 0.0, 0.0),
                (80.0, 0.0, 0.0),
                (80.0, 80.0, 0.0),
                (0.0, 80.0, 10.0),
            ]),
        ])
        config: dict[str, Any] = {
            "printer_settings_id": "Snapmaker U1 (0.4 nozzle)",
            "printer_model": "Snapmaker U1",
            "layer_height": "0.2",
            "filament_colour": ["#FF0000", "#00FF00"],
            "filament_type": ["PLA", "TPU"],
            "filament_settings_id": [
                "Snapmaker PLA @Snapmaker U1",
                "Snapmaker TPU @Snapmaker U1",
            ],
            "filament_max_volumetric_speed": ["25", "12"],
            "slow_down_layer_time": ["8", "30"],
            "z_hop": ["0.2", "0.2"],
            "support_filament": "1",
            "support_interface_filament": "1",
            "wall_filament": "1",
            "sparse_infill_filament": "2",
            "prime_tower_enable": "1",
            "prime_tower_brim_width": "2.0",
        }
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(
            make_3mf(config=config, extra_entries={"3D/3dmodel.model": model_xml})
        )

        _run_fix(input_path, output_path, "peba-safe")

        updated = _read_config(output_path)
        assert float(updated["prime_tower_brim_width"]) == 5.0
