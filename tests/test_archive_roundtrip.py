"""Tests for archive read/write round-trip fidelity."""

from __future__ import annotations

import io
import zipfile

from u1kit.archive import read_3mf, write_3mf
from u1kit.config import emit_config, parse_config

from tests.conftest import make_3mf


class TestArchiveRoundtrip:
    """Non-config entries must survive read/write byte-identical."""

    def test_non_config_entries_preserved(self) -> None:
        """Arbitrary non-config entries should be byte-identical after round-trip."""
        fake_png = b"\x89PNG\r\n\x1a\n" + b"x" * 1000
        fake_model = b"<model>some mesh vertices</model>"
        fake_rels = b'<?xml version="1.0"?><Relationships/>'

        original = make_3mf(
            extra_entries={
                "Metadata/plate_1/thumbnail.png": fake_png,
                "3D/3dmodel.model": fake_model,
                "_rels/.rels": fake_rels,
            }
        )

        # Read and write back
        archive = read_3mf(io.BytesIO(original))
        output = io.BytesIO()
        write_3mf(archive, output)

        # Verify non-config entries
        output.seek(0)
        with zipfile.ZipFile(output, "r") as zf:
            assert zf.read("Metadata/plate_1/thumbnail.png") == fake_png
            assert zf.read("3D/3dmodel.model") == fake_model
            assert zf.read("_rels/.rels") == fake_rels

    def test_config_edit_preserves_others(self) -> None:
        """Editing config should not affect other entries."""
        fake_data = b"binary blob " * 100

        original = make_3mf(
            extra_entries={"3D/3dmodel.model": fake_data}
        )

        archive = read_3mf(io.BytesIO(original))

        # Modify config
        config = parse_config(archive.config_bytes)
        config["new_key"] = "new_value"
        archive.config_bytes = emit_config(config)

        # Write and verify
        output = io.BytesIO()
        write_3mf(archive, output)

        output.seek(0)
        with zipfile.ZipFile(output, "r") as zf:
            assert zf.read("3D/3dmodel.model") == fake_data
            roundtrip_config = parse_config(zf.read("Metadata/project_settings.config"))
            assert roundtrip_config["new_key"] == "new_value"

    def test_entry_order_preserved(self) -> None:
        """Entries should appear in the same order after round-trip."""
        original = make_3mf(
            extra_entries={
                "3D/3dmodel.model": b"model",
                "Metadata/custom.xml": b"<custom/>",
                "Textures/tex1.png": b"png_data",
            }
        )

        archive = read_3mf(io.BytesIO(original))
        output = io.BytesIO()
        write_3mf(archive, output)

        output.seek(0)
        with zipfile.ZipFile(output, "r") as zf:
            names = zf.namelist()

        # Verify the relative order is maintained
        orig_zf = zipfile.ZipFile(io.BytesIO(original), "r")
        orig_names = orig_zf.namelist()
        orig_zf.close()

        assert names == orig_names

    def test_empty_config_still_round_trips(self) -> None:
        """An empty config dict should round-trip correctly."""
        original = make_3mf(config={})
        archive = read_3mf(io.BytesIO(original))

        config = parse_config(archive.config_bytes)
        assert config == {}

        output = io.BytesIO()
        write_3mf(archive, output)
        output.seek(0)

        archive2 = read_3mf(output)
        assert parse_config(archive2.config_bytes) == {}
