"""Tests for the CLI entry points."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from click.testing import CliRunner

from tests.conftest import make_bambu_4color_3mf, make_full_spectrum_3mf
from u1kit.cli import main


class TestLint:
    """u1kit lint command."""

    def test_lint_bambu_file_reports_failures(self, tmp_path: Path) -> None:
        """Linting a Bambu file should report failures."""
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path)])

        assert result.exit_code == 1  # Has failures
        assert "A2" in result.output
        assert "FAIL" in result.output

    def test_lint_json_output(self, tmp_path: Path) -> None:
        """--json flag produces valid JSON output."""
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path), "--json"])

        data = json.loads(result.output)
        assert "results" in data
        assert "summary" in data
        assert data["summary"]["fail"] > 0

    def test_lint_json_has_schema_version(self, tmp_path: Path) -> None:
        """JSON output must include schema_version field."""
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path), "--json"])

        data = json.loads(result.output)
        assert data["schema_version"] == "1"

    def test_lint_clean_file_passes(self, tmp_path: Path) -> None:
        """A properly configured file should pass lint."""
        from tests.conftest import make_3mf

        config = {
            "printer_settings_id": "Snapmaker U1",
            "printer_model": "Snapmaker U1",
            "machine_start_gcode": "G28\n",
            "machine_end_gcode": "M400\n",
            "change_filament_gcode": "T[next_extruder]\n",
            "layer_change_gcode": ";LAYER_CHANGE\n",
            "filament_colour": "#FF0000;#00FF00",
            "filament_map": [1, 2],
        }
        path = tmp_path / "clean.3mf"
        path.write_bytes(make_3mf(config=config))

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path)])

        assert result.exit_code == 0


class TestFix:
    """u1kit fix command."""

    def test_fix_bambu_file(self, tmp_path: Path) -> None:
        """Fix a Bambu file and verify output passes lint."""
        input_path = tmp_path / "input.3mf"
        output_path = tmp_path / "output.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()

        # Fix
        result = runner.invoke(
            main, ["fix", str(input_path), "--out", str(output_path)]
        )
        assert result.exit_code == 0
        assert output_path.exists()

        # Lint the output
        lint_result = runner.invoke(main, ["lint", str(output_path)])
        assert lint_result.exit_code == 0, f"Lint failures after fix:\n{lint_result.output}"

    def test_fix_dry_run(self, tmp_path: Path) -> None:
        """--dry-run should not write output."""
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())
        original = path.read_bytes()

        runner = CliRunner()
        result = runner.invoke(main, ["fix", str(path), "--dry-run"])

        assert result.exit_code == 0
        # File should not be modified (dry-run doesn't write)
        assert path.read_bytes() == original

    def test_fix_json_output(self, tmp_path: Path) -> None:
        """--json flag produces valid JSON from fix command."""
        input_path = tmp_path / "input.3mf"
        output_path = tmp_path / "output.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(input_path), "--out", str(output_path), "--json"]
        )

        # The JSON output is the full response (no trailing text when --json is used)
        data = json.loads(result.output)
        assert "results" in data
        assert "fixers" in data

    def test_fix_full_spectrum_d1_heights_equalized(self, tmp_path: Path) -> None:
        """Full Spectrum file with bad bounds: after fix, all heights = uniform."""
        path = tmp_path / "test.3mf"
        out_path = tmp_path / "out.3mf"
        path.write_bytes(make_full_spectrum_3mf(lower_bound="0.04", layer_height="0.2"))

        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(path), "--out", str(out_path)]
        )
        assert result.exit_code == 0

        # Read the output and check config values
        from u1kit.archive import read_3mf
        from u1kit.config import parse_config

        archive = read_3mf(str(out_path))
        config = parse_config(archive.config_bytes)
        assert config["layer_height"] == "0.2"
        assert config["mixed_filament_height_lower_bound"] == "0.2"
        assert config["mixed_filament_height_upper_bound"] == "0.2"

    def test_fix_thumbnail_survives(self, tmp_path: Path) -> None:
        """Fake PNG embedded as thumbnail must survive fix byte-identical."""
        path = tmp_path / "input.3mf"
        out_path = tmp_path / "output.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        expected_png = b"\x89PNG\r\n\x1a\nfake_png_data"

        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(path), "--out", str(out_path)]
        )
        assert result.exit_code == 0

        with zipfile.ZipFile(str(out_path), "r") as zf:
            actual_png = zf.read("Metadata/plate_1/thumbnail.png")
        assert actual_png == expected_png

    def test_fix_uniform_height(self, tmp_path: Path) -> None:
        """--uniform-height should be passed to D1 fixer."""
        path = tmp_path / "test.3mf"
        out_path = tmp_path / "out.3mf"
        path.write_bytes(make_full_spectrum_3mf(lower_bound="0.04", layer_height="0.2"))

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["fix", str(path), "--out", str(out_path), "--uniform-height", "0.16"],
        )
        assert result.exit_code == 0


class TestPresets:
    """u1kit presets command."""

    def test_presets_list(self) -> None:
        """List presets should show bambu-to-u1."""
        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list"])
        assert result.exit_code == 0
        assert "bambu-to-u1" in result.output

    def test_presets_list_json(self) -> None:
        """--json flag should produce valid JSON."""
        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert any(p["name"] == "bambu-to-u1" for p in data)
