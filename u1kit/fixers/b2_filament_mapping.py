"""B2 fixer: Auto-assign filament-to-extruder mapping."""

from __future__ import annotations

from typing import Any

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context


class B2FilamentMappingFixer(Fixer):
    """Assign extruder indices 1–4 by first-use order."""

    @property
    def id(self) -> str:
        return "b2"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        # Determine filament count from filament_colour
        filament_colours = config.get("filament_colour", [])
        if isinstance(filament_colours, str):
            filament_colours = [c for c in filament_colours.split(";") if c]

        count = len(filament_colours)
        if count == 0:
            return

        # Assign extruder indices 1–N (capped at 4)
        mapping = list(range(1, min(count, 4) + 1))

        # If more filaments than extruders, wrap around
        while len(mapping) < count:
            mapping.append(mapping[len(mapping) % 4])

        config["filament_map"] = mapping
