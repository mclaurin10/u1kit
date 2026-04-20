"""F1: info when a used filament's settings_id lacks @Snapmaker U1 lineage.

Snapmaker Orca's "Print Preprocessing" dialog validates filament profiles
before sending a job to the U1. Profiles inherited from a different
printer base (e.g. ``Generic PLA @BBL X1C``) — or from no named base at
all — are rejected with a generic error message, wasting a round trip.

Surfacing this at lint time lets the user rebuild from a Generic U1 base
(or fall back to the SD-card workflow, which bypasses Preprocessing)
before hitting the dialog. Info-only — there's no single-config fix; the
lineage lives inside the Orca profile system, outside the .3mf.

Heuristic (DECISIONS.md items 16, 23): regex ``r" @([A-Za-z0-9 ]+)$"``
applied to each used filament's ``filament_settings_id``. If the match
is absent or its captured suffix is anything other than ``Snapmaker U1``,
emit one info finding per offending slot.
"""

from __future__ import annotations

import re

from u1kit.filaments import get_filament_field, get_used_filament_indices
from u1kit.rules.base import Context, Result, Rule, Severity

SETTINGS_ID_FIELD = "filament_settings_id"
TYPE_FIELD = "filament_type"
LINEAGE_PATTERN = re.compile(r" @([A-Za-z0-9 ]+)$")
SNAPMAKER_LINEAGE = "Snapmaker U1"


class F1PreprocessingLineage(Rule):
    """Info when a used filament lacks @Snapmaker U1 lineage."""

    @property
    def id(self) -> str:
        return "F1"

    @property
    def name(self) -> str:
        return "Print Preprocessing filament lineage"

    def check(self, context: Context) -> list[Result]:
        used = get_used_filament_indices(context.config)
        if not used:
            return []

        results: list[Result] = []
        for i in used:
            settings_id = get_filament_field(context.config, SETTINGS_ID_FIELD, i)
            filament_type = (
                get_filament_field(context.config, TYPE_FIELD, i) or "unknown"
            )
            if not settings_id:
                results.append(
                    Result(
                        rule_id=self.id,
                        severity=Severity.INFO,
                        message=(
                            f"Filament slot {i + 1} ({filament_type}) has no "
                            f"filament_settings_id. Snapmaker Orca's Print "
                            f"Preprocessing dialog may reject this — rebuild "
                            f"from a Generic {filament_type} base or use the "
                            f"SD-card workflow."
                        ),
                        fixer_id=None,
                        diff_preview=None,
                    )
                )
                continue

            match = LINEAGE_PATTERN.search(settings_id)
            if match is None or match.group(1) != SNAPMAKER_LINEAGE:
                results.append(
                    Result(
                        rule_id=self.id,
                        severity=Severity.INFO,
                        message=(
                            f"Filament slot {i + 1} ({filament_type}) lacks "
                            f"@Snapmaker U1 lineage ({settings_id!r}). "
                            f"Snapmaker Orca's Print Preprocessing dialog may "
                            f"reject this — rebuild from a Generic "
                            f"{filament_type} base or use the SD-card "
                            f"workflow."
                        ),
                        fixer_id=None,
                        diff_preview=None,
                    )
                )

        return results
