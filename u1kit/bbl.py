"""Shared Bambu/U1 detection utilities for B3 rule and fixer."""

from __future__ import annotations

import re

U1_RE: re.Pattern[str] = re.compile(r"\bU1\b", re.IGNORECASE)


def is_u1_compatible(value: str) -> bool:
    """True if value contains a U1 word-boundary match."""
    return bool(U1_RE.search(value))


def normalize_compatible_printers(value: str | list[str]) -> list[str]:
    """Normalize compatible_printers to a list.

    Handles both semicolon-separated strings (Bambu/Orca format) and lists.
    """
    if isinstance(value, str):
        return [p.strip() for p in value.split(";") if p.strip()]
    return list(value)


def filter_u1_printers(value: str | list[str]) -> list[str]:
    """Return only U1-compatible entries from a compatible_printers value."""
    return [p for p in normalize_compatible_printers(value) if is_u1_compatible(p)]
