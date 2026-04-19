"""3MF 3D/3dmodel.model XML parser for per-object bounding boxes.

The 3MF core spec stores geometry as ``<object>/<mesh>/<vertices>/<vertex>``
nodes with ``x``, ``y``, ``z`` attributes. Some archives (Bambu-produced
ones) split objects into a root ``3D/3dmodel.model`` file that references
meshes in sub-model files via ``<components>``; we walk every ``*.model``
entry in the archive to collect bounds regardless of where the mesh lives.

Bounds are returned untransformed — the ``<build>/<item transform="...">``
matrix positions the model on the plate but does not change its dimensions,
so XY thinness and footprint dimensions are translation-invariant for the
purposes E1/E2 use them for.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass

_NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"


@dataclass
class ObjectBounds:
    """Axis-aligned bounding box for one ``<object>`` in a 3mf model."""

    id: str
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def thinnest_xy(self) -> float:
        """Smaller of the XY extents — the limiting dimension for wall count."""
        return min(self.max_x - self.min_x, self.max_y - self.min_y)


def parse_model(xml_bytes: bytes) -> list[ObjectBounds]:
    """Parse a 3MF model XML; return bounds for every object with inline mesh.

    Objects that consist solely of ``<components>`` references (no inline
    ``<vertices>``) are skipped — the caller is expected to also parse the
    referenced sub-model file.
    """
    root = ET.fromstring(xml_bytes)
    bounds: list[ObjectBounds] = []
    for obj in root.iter(f"{_NS}object"):
        obj_id = obj.get("id")
        if obj_id is None:
            continue
        vertices = list(obj.iter(f"{_NS}vertex"))
        if not vertices:
            continue
        xs: list[float] = []
        ys: list[float] = []
        zs: list[float] = []
        for v in vertices:
            try:
                xs.append(float(v.get("x") or 0))
                ys.append(float(v.get("y") or 0))
                zs.append(float(v.get("z") or 0))
            except ValueError:
                continue
        if not xs:
            continue
        bounds.append(
            ObjectBounds(
                id=obj_id,
                min_x=min(xs), min_y=min(ys), min_z=min(zs),
                max_x=max(xs), max_y=max(ys), max_z=max(zs),
            )
        )
    return bounds


def total_plate_footprint(bounds: Iterable[ObjectBounds]) -> tuple[float, float]:
    """Width, height of the minimal XY rectangle enclosing every object."""
    items = list(bounds)
    if not items:
        return (0.0, 0.0)
    min_x = min(b.min_x for b in items)
    max_x = max(b.max_x for b in items)
    min_y = min(b.min_y for b in items)
    max_y = max(b.max_y for b in items)
    return (max_x - min_x, max_y - min_y)


def parse_archive_geometry(archive_bytes: bytes) -> list[ObjectBounds]:
    """Aggregate bounds from every ``*.model`` entry in the 3mf archive."""
    bounds: list[ObjectBounds] = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as zf:
        for name in zf.namelist():
            if not name.endswith(".model"):
                continue
            try:
                bounds.extend(parse_model(zf.read(name)))
            except ET.ParseError:
                continue
    return bounds
