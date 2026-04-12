"""A3 fixer: Strip Bambu macros and insert U1 toolchange G-code."""

from __future__ import annotations

import re
from importlib import resources
from typing import Any

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context

_toolchange_gcode: str | None = None


def _load_toolchange_gcode() -> str:
    global _toolchange_gcode
    if _toolchange_gcode is None:
        gcode_file = resources.files("u1kit.data").joinpath("u1_toolchange.gcode")
        _toolchange_gcode = gcode_file.read_text(encoding="utf-8")
    return _toolchange_gcode


# Patterns to strip from G-code fields
STRIP_PATTERNS = [
    re.compile(r"^.*\bM620\b.*$", re.MULTILINE),
    re.compile(r"^.*\bM621\b.*$", re.MULTILINE),
    re.compile(r"^.*\bM623\b.*$", re.MULTILINE),
    re.compile(r"^.*\bAMS\b.*$", re.MULTILINE | re.IGNORECASE),
]

GCODE_FIELDS = (
    "machine_start_gcode",
    "machine_end_gcode",
    "change_filament_gcode",
    "layer_change_gcode",
)


class A3BambuMacrosFixer(Fixer):
    """Strip Bambu AMS macros and replace change_filament_gcode with U1 template."""

    @property
    def id(self) -> str:
        return "a3"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        toolchange = _load_toolchange_gcode()

        for field_name in GCODE_FIELDS:
            value = config.get(field_name, "")
            if not isinstance(value, str):
                continue

            # Strip Bambu-specific lines
            cleaned = value
            for pattern in STRIP_PATTERNS:
                cleaned = pattern.sub("", cleaned)

            # Collapse multiple blank lines
            cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

            if field_name == "change_filament_gcode":
                # Replace entirely with U1 toolchange template
                cleaned = toolchange.strip()

            config[field_name] = cleaned
