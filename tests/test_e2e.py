"""End-to-end verification: synthetic Bambu .3mf → lint → fix → lint clean.

This single coherent sequence exercises the full CLI surface that Phase 1 promises:
lint reports failures on a Bambu input, fix produces a cleaned output, lint on the
output is clean, the JSON shape is stable, and the output .3mf is a valid archive
with the original non-config entries preserved.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from click.testing import CliRunner

from tests.conftest import make_bambu_4color_3mf
from u1kit.cli import main


class TestPhase1EndToEnd:
    """Full Bambu .3mf → u1kit → U1-compatible .3mf pipeline."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        runner = CliRunner()
        input_path = tmp_path / "bambu_input.3mf"
        output_path = tmp_path / "u1_output.3mf"

        # Step 1+2: Build synthetic Bambu .3mf and write to disk.
        input_path.write_bytes(make_bambu_4color_3mf())

        # Step 3: lint the Bambu input — expect failures.
        lint_before = runner.invoke(main, ["lint", str(input_path)])
        assert lint_before.exit_code == 1, (
            f"Expected Bambu input to fail lint, got exit {lint_before.exit_code}\n"
            f"{lint_before.output}"
        )
        assert "FAIL" in lint_before.output

        # Step 4: fix the input, writing to a separate output path.
        fix_result = runner.invoke(
            main, ["fix", str(input_path), "--out", str(output_path)]
        )
        assert fix_result.exit_code == 0, (
            f"Fix failed: exit {fix_result.exit_code}\n{fix_result.output}"
        )
        assert output_path.exists(), "Fix did not write output file"

        # Step 5: lint the fixed output — expect clean.
        lint_after = runner.invoke(main, ["lint", str(output_path)])
        assert lint_after.exit_code == 0, (
            f"Lint failures after fix:\n{lint_after.output}"
        )

        # Step 6: JSON output shape and zero fails.
        lint_json = runner.invoke(main, ["lint", str(output_path), "--json"])
        assert lint_json.exit_code == 0
        data = json.loads(lint_json.output)
        assert data["schema_version"] == "1"
        assert data["summary"]["fail"] == 0
        assert "results" in data
        assert "summary" in data

        # Step 7: output .3mf is a valid ZIP with the expected entries.
        with zipfile.ZipFile(output_path, "r") as zf:
            names = set(zf.namelist())
            assert "Metadata/project_settings.config" in names
            assert "3D/3dmodel.model" in names
            # Thumbnail from the synthetic Bambu fixture must survive round-trip.
            assert "Metadata/plate_1/thumbnail.png" in names
            thumb = zf.read("Metadata/plate_1/thumbnail.png")
            assert thumb == b"\x89PNG\r\n\x1a\nfake_png_data"

    def test_fix_json_output_is_parseable(self, tmp_path: Path) -> None:
        """Fix --json must be valid JSON (no trailing text)."""
        runner = CliRunner()
        input_path = tmp_path / "input.3mf"
        output_path = tmp_path / "output.3mf"
        input_path.write_bytes(make_bambu_4color_3mf())

        result = runner.invoke(
            main,
            ["fix", str(input_path), "--out", str(output_path), "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["schema_version"] == "1"
        assert "fixers" in data
        # At least one fixer must have applied against the Bambu input.
        assert data["fixers"] is not None
        assert any(fr["applied"] for fr in data["fixers"])
