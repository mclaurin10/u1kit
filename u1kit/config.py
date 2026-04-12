"""Parse and emit project_settings.config and filament config JSON."""

from __future__ import annotations

import json
from typing import Any


def parse_config(raw: bytes) -> dict[str, Any]:
    """Parse a .3mf config file (JSON despite the .config extension).

    Args:
        raw: Raw bytes from the archive entry.

    Returns:
        Parsed JSON as a dict.
    """
    return json.loads(raw.decode("utf-8"))  # type: ignore[no-any-return]


def emit_config(data: dict[str, Any]) -> bytes:
    """Serialize config data back to bytes for writing into a .3mf.

    Uses sorted keys and 4-space indent to match Orca Slicer output format.

    Args:
        data: Config dict to serialize.

    Returns:
        UTF-8 encoded JSON bytes.
    """
    text = json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False)
    return (text + "\n").encode("utf-8")
