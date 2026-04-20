"""Sidecar-readiness contract tests for the CLI.

Phase 3 invokes u1kit as a subprocess from Tauri. These tests lock the
pieces of the CLI the GUI depends on: version matching, --json stdout
purity, deterministic exit codes, and the JSON schemas of lint / fix /
presets list. Each of these is public API; breaking them breaks the
GUI's sidecar integration.

Unlike tests/test_cli.py which exercises user-facing behavior, these
tests assert contract properties that only matter when the CLI is
driven programmatically.
"""

from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from pathlib import Path

from click.testing import CliRunner

from tests.conftest import make_bambu_4color_3mf
from u1kit import __version__
from u1kit.cli import main


class TestVersionContract:
    """u1kit --version output must match importlib.metadata.version('u1kit')."""

    def test_version_matches_package(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        # --version prints "<version>\n" (configured via message="%(version)s").
        reported = result.output.strip()
        try:
            expected = pkg_version("u1kit")
        except PackageNotFoundError:
            expected = __version__
        assert reported == expected, f"CLI reported {reported!r}, package is {expected!r}"


class TestJsonStdoutPurity:
    """--json output on stdout must be exactly one parseable JSON object.

    Tauri's Command captures stdout and parses it. Any info/warn/error log
    mixed into stdout breaks json.loads. Logs must go to stderr.
    """

    def test_lint_json_stdout_parses_as_one_object(self, tmp_path: Path) -> None:
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path), "--json"])
        # Expect exit 0 (clean) or 1 (has fails) — both are valid.
        assert result.exit_code in (0, 1)
        # stdout must parse as exactly one JSON object with no log prefix/suffix.
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert data["schema_version"] == "1"

    def test_fix_json_stdout_parses_as_one_object(self, tmp_path: Path) -> None:
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(input_path), "--out", str(output_path), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert data["schema_version"] == "1"

    def test_presets_list_json_stdout_parses_as_one_object(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert data["schema_version"] == "1"
        assert "presets" in data


class TestExitCodes:
    """Exit codes: 0 clean, 1 lint found fails, 2 reserved for internal errors."""

    def test_lint_exit_code_0_when_clean(self, tmp_path: Path) -> None:
        # A config that should lint clean at fail severity.
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
        result = runner.invoke(main, ["lint", str(path), "--json"])
        assert result.exit_code == 0

    def test_lint_exit_code_1_on_fail_severity(self, tmp_path: Path) -> None:
        path = tmp_path / "bambu.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path), "--json"])
        assert result.exit_code == 1


class TestLintJsonContract:
    """lint --json emits the documented schema."""

    def test_schema_has_required_keys(self, tmp_path: Path) -> None:
        path = tmp_path / "test.3mf"
        path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(main, ["lint", str(path), "--json"])
        data = json.loads(result.output)
        assert data["schema_version"] == "1"
        assert "results" in data
        assert "summary" in data
        # Each result has the documented shape.
        for r in data["results"]:
            assert set(r.keys()) >= {
                "rule_id",
                "severity",
                "message",
                "fixer_id",
                "diff_preview",
            }
            assert r["severity"] in ("fail", "warn", "info")


class TestFixJsonContract:
    """fix --json emits the documented schema."""

    def test_schema_has_required_keys(self, tmp_path: Path) -> None:
        input_path = tmp_path / "in.3mf"
        output_path = tmp_path / "out.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        runner = CliRunner()
        result = runner.invoke(
            main, ["fix", str(input_path), "--out", str(output_path), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["schema_version"] == "1"
        assert "results" in data
        assert "fixers" in data
        assert "summary" in data
        for fr in data["fixers"]:
            assert set(fr.keys()) == {"fixer_id", "applied", "message"}


class TestPresetsListJsonContract:
    """presets list --json emits the documented schema."""

    def test_schema_has_required_keys(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list", "--json"])
        data = json.loads(result.output)
        assert data["schema_version"] == "1"
        assert isinstance(data["presets"], list)
        for p in data["presets"]:
            assert set(p.keys()) >= {"name", "description", "source"}
            assert p["source"] in ("bundled", "user")
