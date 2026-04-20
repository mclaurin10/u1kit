"""Tests for the CLI entry points."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
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
            "printer_settings_id": "Snapmaker U1 (0.4 nozzle)",
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


class TestUserPresetLoader:
    """User-defined presets from platformdirs user config dir."""

    def test_user_preset_loads(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "my-custom.yaml").write_text(
            "name: my-custom\n"
            "description: user-defined\n"
            "rules: [A2]\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("u1kit.cli._user_preset_dir", lambda: user_dir)

        from u1kit.cli import _load_preset

        data = _load_preset("my-custom")
        assert data["description"] == "user-defined"
        assert data["rules"] == ["A2"]

    def test_user_preset_overrides_bundled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "bambu-to-u1.yaml").write_text(
            "name: bambu-to-u1\n"
            "description: overridden by user\n"
            "rules: [A2]\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("u1kit.cli._user_preset_dir", lambda: user_dir)

        from u1kit.cli import _load_preset

        data = _load_preset("bambu-to-u1")
        assert data["description"] == "overridden by user"

    def test_presets_list_tags_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "custom.yaml").write_text(
            "name: custom\n"
            "description: my custom one\n"
            "rules: [A2]\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("u1kit.cli._user_preset_dir", lambda: user_dir)

        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list"])
        assert result.exit_code == 0
        assert "bundled" in result.output
        assert "user" in result.output
        assert "custom" in result.output
        assert "bambu-to-u1" in result.output

    def test_presets_list_json_tags_source(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "custom.yaml").write_text(
            "name: custom\ndescription: x\nrules: [A2]\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("u1kit.cli._user_preset_dir", lambda: user_dir)

        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        names = {p["name"]: p for p in data}
        assert names["custom"]["source"] == "user"
        assert names["bambu-to-u1"]["source"] == "bundled"

    def test_nonexistent_user_dir_falls_back_to_bundled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "u1kit.cli._user_preset_dir", lambda: tmp_path / "does-not-exist"
        )
        from u1kit.cli import _load_preset

        data = _load_preset("bambu-to-u1")
        assert data["name"] == "bambu-to-u1"


class TestPresetOptions:
    """Preset-level options flow through to Context.options (for E3 opt-in fixer)."""

    def test_preset_options_reach_fixer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from tests.conftest import make_3mf, make_model_xml

        # User preset with options → rules: [E3], options: {e3_auto_bump: true}.
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "e3-bump.yaml").write_text(
            "name: e3-bump\n"
            "description: enable E3 brim bump for tests\n"
            "rules: [E3]\n"
            "options:\n"
            "  e3_auto_bump: true\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("u1kit.cli._user_preset_dir", lambda: user_dir)

        # Small-plate fixture: 80x80 mm bounding box, prime tower enabled, thin brim.
        model_xml = make_model_xml([
            ("1", [
                (0.0, 0.0, 0.0),
                (80.0, 0.0, 0.0),
                (80.0, 80.0, 0.0),
                (0.0, 80.0, 10.0),
            ]),
        ])
        config: dict[str, Any] = {
            "printer_settings_id": "Snapmaker U1",
            "printer_model": "Snapmaker U1",
            "prime_tower_enable": "1",
            "prime_tower_brim_width": "2.0",
        }
        archive_bytes = make_3mf(
            config=config,
            extra_entries={"3D/3dmodel.model": model_xml},
        )
        input_path = tmp_path / "input.3mf"
        output_path = tmp_path / "output.3mf"
        input_path.write_bytes(archive_bytes)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["fix", str(input_path), "--preset", "e3-bump", "--out", str(output_path)],
        )
        assert result.exit_code == 0, f"fix failed:\n{result.output}"

        # Re-parse the output and verify the brim was bumped to 5.0.
        with zipfile.ZipFile(output_path) as zf:
            updated_config = json.loads(
                zf.read("Metadata/project_settings.config").decode("utf-8")
            )
        assert float(updated_config["prime_tower_brim_width"]) == 5.0
