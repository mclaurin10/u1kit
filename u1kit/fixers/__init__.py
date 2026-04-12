"""Fixer registry."""

from __future__ import annotations

from u1kit.fixers.a2_printer_profile import A2PrinterProfileFixer
from u1kit.fixers.a3_bambu_macros import A3BambuMacrosFixer
from u1kit.fixers.b1_filament_count import B1FilamentCountFixer
from u1kit.fixers.b2_filament_mapping import B2FilamentMappingFixer
from u1kit.fixers.b3_bbl_fields import B3BblFieldsFixer
from u1kit.fixers.base import Fixer, FixerResult, FixMode, Pipeline
from u1kit.fixers.d1_mixed_height_bounds import D1MixedHeightBoundsFixer

__all__ = [
    "FIXERS",
    "Fixer",
    "FixerResult",
    "FixMode",
    "Pipeline",
    "get_fixer",
]

# All registered fixers
FIXERS: list[type[Fixer]] = [
    A2PrinterProfileFixer,
    A3BambuMacrosFixer,
    B1FilamentCountFixer,
    B2FilamentMappingFixer,
    B3BblFieldsFixer,
    D1MixedHeightBoundsFixer,
]

_FIXER_MAP: dict[str, Fixer] = {cls().id: cls() for cls in FIXERS}


def get_fixer(fixer_id: str) -> Fixer:
    """Get a fixer instance by its ID."""
    if fixer_id not in _FIXER_MAP:
        raise KeyError(f"Unknown fixer ID: {fixer_id!r}")
    return _FIXER_MAP[fixer_id]


def get_fixer_map() -> dict[str, Fixer]:
    """Get the complete fixer ID -> instance map."""
    return dict(_FIXER_MAP)
