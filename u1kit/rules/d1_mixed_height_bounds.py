"""D1: Mixed filament height bounds must be ≥ layer height."""

from __future__ import annotations

from u1kit.rules.base import Context, Result, Rule, Severity

DEFAULT_UNIFORM_HEIGHT = 0.2


class D1MixedHeightBounds(Rule):
    """Check that mixed_filament_height_lower_bound >= layer_height."""

    @property
    def id(self) -> str:
        return "D1"

    @property
    def name(self) -> str:
        return "Mixed height bounds"

    def check(self, context: Context) -> list[Result]:
        config = context.config

        # Only relevant if mixed height keys exist (Full Spectrum source)
        lower_key = "mixed_filament_height_lower_bound"
        if lower_key not in config:
            return []

        try:
            lower_bound = float(config[lower_key])
        except (TypeError, ValueError):
            return [
                Result(
                    rule_id=self.id,
                    severity=Severity.FAIL,
                    message=f"{lower_key} is not a valid number: {config[lower_key]!r}",
                )
            ]

        try:
            layer_height = float(config.get("layer_height", 0.2))
        except (TypeError, ValueError):
            layer_height = 0.2

        if lower_bound >= layer_height:
            return []

        uniform = context.options.get("uniform_height", DEFAULT_UNIFORM_HEIGHT)
        upper_bound = config.get("mixed_filament_height_upper_bound", "?")

        diff = (
            f"layer_height={layer_height}, "
            f"lower_bound={lower_bound}, "
            f"upper_bound={upper_bound} "
            f"-> all locked to {uniform}"
        )

        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=f"mixed_filament_height_lower_bound ({lower_bound}) < "
                f"layer_height ({layer_height}). "
                f"Will lock all three to {uniform} mm.",
                fixer_id="d1",
                diff_preview=diff,
            )
        ]
