"""B1: Filament count must be ≤ 4. Report-only in Phase 1."""

from __future__ import annotations

from u1kit.rules.base import Context, Result, Rule, Severity


class B1FilamentCount(Rule):
    """Check that no more than 4 filaments are used."""

    @property
    def id(self) -> str:
        return "B1"

    @property
    def name(self) -> str:
        return "Filament count"

    def check(self, context: Context) -> list[Result]:
        config = context.config

        # Filament count determined by filament_colour array length
        filament_colours = config.get("filament_colour", [])
        if isinstance(filament_colours, str):
            # Sometimes stored as semicolon-separated string
            filament_colours = [c for c in filament_colours.split(";") if c]

        count = len(filament_colours)
        if count <= 4:
            return []

        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=(
                    f"File uses {count} filaments but U1 supports max 4. "
                    f"Run with --interactive to merge them."
                ),
                fixer_id="b1",
            )
        ]
