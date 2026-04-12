"""Test fixtures and helpers for synthesizing .3mf archives."""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any

import pytest


def make_3mf(
    config: dict[str, Any] | None = None,
    filament_configs: dict[str, dict[str, Any]] | None = None,
    extra_entries: dict[str, bytes] | None = None,
) -> bytes:
    """Build a minimal .3mf ZIP archive in memory.

    Args:
        config: Contents of Metadata/project_settings.config (dict -> JSON).
        filament_configs: Mapping of archive path -> filament config dict.
        extra_entries: Additional entries to include (path -> raw bytes).

    Returns:
        Bytes of the complete ZIP archive.
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Always include a minimal 3D model
        if extra_entries and "3D/3dmodel.model" in extra_entries:
            pass  # will be added below
        else:
            zf.writestr("3D/3dmodel.model", b"<model>fake model data</model>")

        # Content types (required by .3mf spec)
        zf.writestr(
            "[Content_Types].xml",
            b'<?xml version="1.0"?><Types></Types>',
        )

        # Project settings config
        if config is None:
            config = _default_bambu_config()
        config_json = json.dumps(config, indent=4, sort_keys=True).encode("utf-8")
        zf.writestr("Metadata/project_settings.config", config_json)

        # Filament configs
        if filament_configs:
            for path, fil_data in filament_configs.items():
                fil_json = json.dumps(fil_data, indent=4, sort_keys=True).encode("utf-8")
                zf.writestr(path, fil_json)

        # Extra entries
        if extra_entries:
            for path, data in extra_entries.items():
                if path not in (
                    "Metadata/project_settings.config",
                    "3D/3dmodel.model",
                    "[Content_Types].xml",
                ):
                    zf.writestr(path, data)

    return buf.getvalue()


def _default_bambu_config() -> dict[str, Any]:
    """Return a config that looks like a typical Bambu 4-color Makerworld file."""
    return {
        "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",
        "printer_model": "Bambu Lab X1 Carbon",
        "printable_area": "0x0,256x0,256x256,0x256",
        "printable_height": "250",
        "machine_max_acceleration_x": "20000",
        "machine_max_acceleration_y": "20000",
        "machine_max_acceleration_z": "1500",
        "machine_max_speed_x": "500",
        "machine_max_speed_y": "500",
        "machine_max_speed_z": "30",
        "machine_max_jerk_x": "9",
        "machine_max_jerk_y": "9",
        "machine_max_jerk_z": "3",
        "layer_height": "0.2",
        "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        "machine_start_gcode": "M620 S[next_extruder]A\nG28\nM621 S[next_extruder]A\n",
        "machine_end_gcode": "M400\nM104 S0\n",
        "change_filament_gcode": "M620 S[next_extruder]A\nT[next_extruder]\nM621 S[next_extruder]A\n",
        "layer_change_gcode": ";LAYER_CHANGE\n;Z:[layer_z]\n",
        "bbl_use_printhost": "1",
        "compatible_printers": "Bambu Lab X1 Carbon 0.4 nozzle",
    }


def make_bambu_4color_3mf() -> bytes:
    """Build a typical Bambu 4-color .3mf for testing the full pipeline."""
    return make_3mf(
        config=_default_bambu_config(),
        extra_entries={
            "Metadata/plate_1/thumbnail.png": b"\x89PNG\r\n\x1a\nfake_png_data",
            "3D/3dmodel.model": b"<model>realistic mesh data here</model>",
        },
    )


def make_full_spectrum_3mf(
    lower_bound: str = "0.04",
    layer_height: str = "0.2",
    upper_bound: str = "0.4",
) -> bytes:
    """Build a Full Spectrum .3mf with mixed height settings."""
    config = {
        "printer_settings_id": "Snapmaker U1",
        "printer_model": "Snapmaker U1",
        "printable_area": "0x0,320x0,320x320,0x320",
        "printable_height": "340",
        "layer_height": layer_height,
        "mixed_filament_height_lower_bound": lower_bound,
        "mixed_filament_height_upper_bound": upper_bound,
        "mixed_filament_height_layer_height": layer_height,
        "filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00",
        "filament_map": [1, 2, 3, 4],
        "machine_start_gcode": "G28\n",
        "machine_end_gcode": "M400\n",
        "change_filament_gcode": "T[next_extruder]\n",
        "layer_change_gcode": ";LAYER_CHANGE\n",
    }
    return make_3mf(config=config)


@pytest.fixture
def bambu_4color_3mf_bytes() -> bytes:
    """Fixture: Bambu 4-color .3mf as bytes."""
    return make_bambu_4color_3mf()


@pytest.fixture
def full_spectrum_3mf_bytes() -> bytes:
    """Fixture: Full Spectrum .3mf with mixed height bounds issue."""
    return make_full_spectrum_3mf(lower_bound="0.04", layer_height="0.2")


@pytest.fixture
def tmp_3mf(tmp_path: Any, bambu_4color_3mf_bytes: bytes) -> Any:
    """Write a Bambu .3mf to a temp file and return its path."""
    path = tmp_path / "test.3mf"
    path.write_bytes(bambu_4color_3mf_bytes)
    return path
