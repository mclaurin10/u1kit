"""B1 fixer: interactively merge filaments down to the 4-slot U1 maximum.

Algorithm: greedily find the pair with the smallest CIEDE2000 color
distance, merge the higher-index slot into the lower-index one, and repeat
until at most 4 filaments remain. Each merge pops the higher slot from
every parallel-array field and remaps scalar selectors (wall, support,
infill, wipe_tower) to preserve the original intent where possible.

This fixer is destructive and refuses to run in AUTO mode unless the
caller explicitly opts in via ``b1_force_merge=True`` in
``context.options``. Interactive mode (``b1_interactive=True``) prompts
once per proposed merge; skipping a merge adds that pair to a reject set
that is cleared after any successful merge (since indices shift).
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

import click

from u1kit.color import hex_distance
from u1kit.filaments import (
    SELECTOR_FIELDS,
    get_filament_count,
    get_filament_field,
    parse_scalar_index,
    pop_filament_slot,
)
from u1kit.fixers.base import Fixer, FixerAbort
from u1kit.interactive import FixAction, prompt_fix
from u1kit.rules.base import Context, Result, Severity


class B1MergeRequiresConsent(FixerAbort):
    """Raised when B1 is invoked without interactive or explicit-force consent."""


class B1FilamentCountFixer(Fixer):
    """Merge filaments down to 4 using CIEDE2000-closest-first selection."""

    @property
    def id(self) -> str:
        return "b1"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        if get_filament_count(config) <= 4:
            return

        interactive = bool(context.options.get("b1_interactive"))
        force = bool(context.options.get("b1_force_merge"))
        if not interactive and not force:
            raise B1MergeRequiresConsent(
                "B1 merge requires --interactive or explicit consent; "
                "refusing to auto-merge filaments"
            )

        rejected: set[tuple[int, int]] = set()

        while get_filament_count(config) > 4:
            pair = self._closest_pair(config, rejected)
            if pair is None:
                break

            dst, src, distance = pair
            if interactive:
                result = self._describe_merge(config, dst, src, distance)
                action = prompt_fix(result, self)
                if action is FixAction.SKIP:
                    rejected.add((dst, src))
                    continue
                if action is FixAction.QUIT:
                    raise click.Abort()

            pop_filament_slot(config, src, target_index=dst)
            rejected.clear()

    def _closest_pair(
        self,
        config: dict[str, Any],
        rejected: set[tuple[int, int]],
    ) -> tuple[int, int, float] | None:
        count = get_filament_count(config)
        if count < 2:
            return None

        best: tuple[int, int, float] | None = None
        for i, j in combinations(range(count), 2):
            if (i, j) in rejected:
                continue
            color_i = get_filament_field(config, "filament_colour", i)
            color_j = get_filament_field(config, "filament_colour", j)
            if color_i is None or color_j is None:
                continue
            try:
                dist = hex_distance(color_i, color_j)
            except ValueError:
                continue
            if best is None or dist < best[2]:
                best = (i, j, dist)
        return best

    def _describe_merge(
        self,
        config: dict[str, Any],
        dst: int,
        src: int,
        distance: float,
    ) -> Result:
        color_dst = get_filament_field(config, "filament_colour", dst) or "?"
        color_src = get_filament_field(config, "filament_colour", src) or "?"
        type_dst = get_filament_field(config, "filament_type", dst) or "?"
        type_src = get_filament_field(config, "filament_type", src) or "?"

        affected: list[str] = []
        for field in SELECTOR_FIELDS:
            raw = config.get(field)
            if raw is None:
                continue
            if parse_scalar_index(raw) == src:
                affected.append(field)

        preview = (
            f"Affected selectors: {', '.join(affected)}"
            if affected
            else "No selector currently references this filament"
        )

        message = (
            f"Merge filament {src + 1} ({color_src}, {type_src}) "
            f"-> filament {dst + 1} ({color_dst}, {type_dst})  "
            f"dE={distance:.2f}"
        )

        return Result(
            rule_id="B1",
            severity=Severity.FAIL,
            message=message,
            fixer_id="b1",
            diff_preview=preview,
        )
