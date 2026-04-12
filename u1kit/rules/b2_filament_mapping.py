"""B2: Every used filament must have an extruder index in 1–4."""

from __future__ import annotations

from u1kit.rules.base import Context, Result, Rule, Severity


class B2FilamentMapping(Rule):
    """Check that all filaments have valid extruder mapping."""

    @property
    def id(self) -> str:
        return "B2"

    @property
    def name(self) -> str:
        return "Filament mapping"

    def check(self, context: Context) -> list[Result]:
        config = context.config

        # Get filament colours to determine count
        filament_colours = config.get("filament_colour", [])
        if isinstance(filament_colours, str):
            filament_colours = [c for c in filament_colours.split(";") if c]

        filament_count = len(filament_colours)
        if filament_count == 0:
            return []

        # Check flush_into_objects / filament_map for extruder assignments
        # In Orca/Bambu .3mf, extruder mapping is typically in flush_into_objects
        # or via a filament_map-like structure. We check for explicit extruder indices.
        extruder_map = config.get("filament_map", [])
        if isinstance(extruder_map, str):
            # Could be semicolon-separated
            parts = [p.strip() for p in extruder_map.split(";") if p.strip()]
            extruder_map = []
            for p in parts:
                try:
                    extruder_map.append(int(p))
                except ValueError:
                    extruder_map.append(0)

        problems: list[str] = []

        if not extruder_map:
            problems.append(
                f"No filament_map defined for {filament_count} filament(s). "
                f"Extruder indices must be assigned (1–4)."
            )
        else:
            for i, idx in enumerate(extruder_map):
                if not isinstance(idx, int) or idx < 1 or idx > 4:
                    problems.append(
                        f"Filament {i + 1}: extruder index {idx!r} is not in 1–4."
                    )

        if not problems:
            return []

        diff = "\n".join(problems)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=f"Filament-to-extruder mapping issues:\n{diff}",
                fixer_id="b2",
                diff_preview=diff,
            )
        ]
