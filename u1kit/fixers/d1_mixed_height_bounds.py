"""D1 fixer: Lock mixed height bounds to uniform value."""

from __future__ import annotations

from typing import Any

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context

DEFAULT_UNIFORM_HEIGHT = 0.2


class D1MixedHeightBoundsFixer(Fixer):
    """Lock layer_height, lower_bound, and upper_bound to a uniform value."""

    @property
    def id(self) -> str:
        return "d1"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        uniform = context.options.get("uniform_height", DEFAULT_UNIFORM_HEIGHT)
        uniform_str = str(uniform)

        config["layer_height"] = uniform_str
        config["mixed_filament_height_lower_bound"] = uniform_str
        config["mixed_filament_height_upper_bound"] = uniform_str
