"""E1: warn when an object's XY footprint is too thin for its wall line width.

When ``thinnest_xy / outer_wall_line_width < 3`` there is not enough width
to lay even a single-perimeter outer wall with inner reinforcement, so the
part either prints hollow or with merged walls that hide surface detail.
This is a geometry check — there is no single-config fix, so the rule is
warn-only.
"""

from __future__ import annotations

from u1kit.rules.base import Context, Result, Rule, Severity

OUTER_WALL_FIELD = "outer_wall_line_width"
RATIO_THRESHOLD = 3.0


def _parse_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


class E1ThinFeature(Rule):
    """Warn on objects where thinnest_xy / outer_wall_line_width < 3."""

    @property
    def id(self) -> str:
        return "E1"

    @property
    def name(self) -> str:
        return "Thin feature relative to wall line width"

    def check(self, context: Context) -> list[Result]:
        if context.geometry_bounds is None or not context.geometry_bounds:
            return []
        line_width = _parse_float(context.config.get(OUTER_WALL_FIELD))
        if line_width is None or line_width <= 0:
            return []

        offenders: list[str] = []
        for bounds in context.geometry_bounds:
            thinnest = bounds.thinnest_xy
            if thinnest <= 0:
                continue
            ratio = thinnest / line_width
            if ratio < RATIO_THRESHOLD:
                offenders.append(
                    f"object {bounds.id}: thinnest_xy={thinnest:g} mm / "
                    f"outer_wall_line_width={line_width:g} mm = {ratio:.2f} "
                    f"(< {RATIO_THRESHOLD:g})"
                )

        if not offenders:
            return []

        diff = "\n".join(offenders)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.WARN,
                message=(
                    "Thin features detected — walls may merge or print hollow:\n"
                    + diff
                ),
                fixer_id=None,
                diff_preview=diff,
            )
        ]
