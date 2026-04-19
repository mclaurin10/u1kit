"""Parser for the ``mixed_filament_definitions`` field.

Each Snapmaker U1 / Full Spectrum mixed-blend definition is encoded as a
semicolon-separated list of comma-separated records. Positions 0, 1 hold the
two filament slot indices; position 4 holds the mix ratio (percent). Positions
2, 3, 5-11 carry meanings we do not need to interpret — we preserve them
verbatim so round-trips do not drop fields.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MixedBlend:
    """One parsed entry from ``mixed_filament_definitions``."""

    filament_a: int
    filament_b: int
    ratio_percent: int
    raw_fields: tuple[str, ...]


def parse_mixed_definitions(raw: str) -> list[MixedBlend]:
    """Parse the raw field into typed blend records.

    Entries with fewer than 5 comma-separated fields, or entries whose typed
    positions (0, 1, 4) are not valid integers, are silently skipped — the
    caller gets only the blends it can act on.
    """
    if not raw or not raw.strip():
        return []

    blends: list[MixedBlend] = []
    for entry in raw.split(";"):
        if not entry.strip():
            continue
        fields = tuple(entry.split(","))
        if len(fields) < 5:
            continue
        try:
            filament_a = int(fields[0])
            filament_b = int(fields[1])
            ratio_percent = int(fields[4])
        except ValueError:
            continue
        blends.append(
            MixedBlend(
                filament_a=filament_a,
                filament_b=filament_b,
                ratio_percent=ratio_percent,
                raw_fields=fields,
            )
        )
    return blends
