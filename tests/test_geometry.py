"""Tests for u1kit.geometry — 3MF model XML parser."""

from __future__ import annotations

from u1kit.geometry import (
    ObjectBounds,
    parse_archive_geometry,
    parse_model,
    total_plate_footprint,
)


def _make_model_xml(objects: list[tuple[str, list[tuple[float, float, float]]]]) -> bytes:
    """Build a minimal 3MF model XML with the given objects and vertices."""
    ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<model unit="millimeter" xmlns="{ns}">',
        "<resources>",
    ]
    for obj_id, verts in objects:
        parts.append(f'<object id="{obj_id}" type="model"><mesh><vertices>')
        for x, y, z in verts:
            parts.append(f'<vertex x="{x}" y="{y}" z="{z}"/>')
        parts.append("</vertices></mesh></object>")
    parts.append("</resources>")
    parts.append("<build/>")
    parts.append("</model>")
    return "".join(parts).encode("utf-8")


class TestParseModel:
    """Parse a single 3dmodel.model XML document."""

    def test_empty_model(self) -> None:
        xml = _make_model_xml([])
        assert parse_model(xml) == []

    def test_single_object(self) -> None:
        xml = _make_model_xml([
            ("1", [(0.0, 0.0, 0.0), (10.0, 5.0, 2.0), (5.0, 2.5, 1.0)]),
        ])
        bounds = parse_model(xml)
        assert len(bounds) == 1
        b = bounds[0]
        assert b.id == "1"
        assert b.min_x == 0.0
        assert b.min_y == 0.0
        assert b.min_z == 0.0
        assert b.max_x == 10.0
        assert b.max_y == 5.0
        assert b.max_z == 2.0

    def test_multiple_objects(self) -> None:
        xml = _make_model_xml([
            ("1", [(0.0, 0.0, 0.0), (1.0, 1.0, 1.0)]),
            ("7", [(10.0, 10.0, 10.0), (20.0, 30.0, 40.0)]),
        ])
        bounds = parse_model(xml)
        assert len(bounds) == 2
        ids = {b.id for b in bounds}
        assert ids == {"1", "7"}

    def test_skips_component_only_objects(self) -> None:
        """Objects with no inline mesh (only component refs) produce no bounds."""
        ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<model xmlns="{ns}">'
            "<resources>"
            '<object id="2" type="model"><components>'
            '<component objectid="1"/>'
            "</components></object>"
            "</resources><build/></model>"
        ).encode()
        assert parse_model(xml) == []

    def test_thinnest_xy(self) -> None:
        bounds = ObjectBounds(
            id="1",
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=100.0, max_y=5.0, max_z=50.0,
        )
        assert bounds.thinnest_xy == 5.0

    def test_thinnest_xy_uses_xy_only(self) -> None:
        bounds = ObjectBounds(
            id="1",
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=10.0, max_y=20.0, max_z=1.0,
        )
        assert bounds.thinnest_xy == 10.0


class TestTotalPlateFootprint:
    """Aggregate plate footprint from per-object bounds."""

    def test_empty_bounds_returns_zero(self) -> None:
        assert total_plate_footprint([]) == (0.0, 0.0)

    def test_single_object_footprint(self) -> None:
        b = ObjectBounds(
            id="1",
            min_x=10.0, min_y=20.0, min_z=0.0,
            max_x=30.0, max_y=55.0, max_z=5.0,
        )
        assert total_plate_footprint([b]) == (20.0, 35.0)

    def test_multiple_objects_envelope(self) -> None:
        b1 = ObjectBounds(
            id="1",
            min_x=0.0, min_y=0.0, min_z=0.0,
            max_x=10.0, max_y=10.0, max_z=5.0,
        )
        b2 = ObjectBounds(
            id="2",
            min_x=50.0, min_y=-5.0, min_z=0.0,
            max_x=60.0, max_y=5.0, max_z=5.0,
        )
        width, height = total_plate_footprint([b1, b2])
        assert width == 60.0  # 60 - 0
        assert height == 15.0  # 10 - (-5)


class TestParseArchiveGeometry:
    """Walk every .model file in a 3mf archive and collect ObjectBounds."""

    def test_root_model_with_inline_mesh(self) -> None:
        import io
        import zipfile

        xml = _make_model_xml([
            ("1", [(0.0, 0.0, 0.0), (5.0, 5.0, 5.0)]),
        ])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("3D/3dmodel.model", xml)
            zf.writestr("[Content_Types].xml", b"<Types/>")

        bounds = parse_archive_geometry(buf.getvalue())
        assert len(bounds) == 1
        assert bounds[0].id == "1"

    def test_nested_model_files(self) -> None:
        import io
        import zipfile

        ns = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
        root_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<model xmlns="{ns}">'
            "<resources>"
            '<object id="2" type="model"><components>'
            '<component objectid="1"/>'
            "</components></object>"
            "</resources><build/></model>"
        ).encode()
        sub_xml = _make_model_xml([
            ("1", [(0.0, 0.0, 0.0), (3.0, 4.0, 5.0)]),
        ])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("3D/3dmodel.model", root_xml)
            zf.writestr("3D/Objects/sub.model", sub_xml)
            zf.writestr("[Content_Types].xml", b"<Types/>")

        bounds = parse_archive_geometry(buf.getvalue())
        assert len(bounds) == 1
        assert bounds[0].id == "1"
        assert bounds[0].max_x == 3.0

    def test_missing_model_returns_empty(self) -> None:
        import io
        import zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", b"<Types/>")
        assert parse_archive_geometry(buf.getvalue()) == []
