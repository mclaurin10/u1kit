"""B5 fixer: reassign flexible support selectors to the best rigid alternative.

Walks ``support_filament`` and ``support_interface_filament`` and, for each
that points at a flexible slot, redirects it to the preferred rigid
alternative (PLA first, then PETG/ABS/ASA/PC; see
``u1kit.filaments.RIGID_PREFERRED``). A no-op if no rigid alternative
exists in the filament list.
"""

from __future__ import annotations

from typing import Any

from u1kit.filaments import (
    find_rigid_alternative,
    get_filament_field,
    is_flexible,
    parse_scalar_index,
)
from u1kit.fixers.base import Fixer
from u1kit.rules.b5_flexible_support import SUPPORT_SELECTORS
from u1kit.rules.base import Context


class B5FlexibleSupportFixer(Fixer):
    """Swap flexible support selectors to the best rigid alternative."""

    @property
    def id(self) -> str:
        return "b5"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        for field in SUPPORT_SELECTORS:
            idx = parse_scalar_index(config.get(field))
            if idx is None:
                continue
            ftype = get_filament_field(config, "filament_type", idx)
            if not is_flexible(ftype):
                continue
            alt = find_rigid_alternative(config, exclude_index=idx)
            if alt is None:
                continue
            config[field] = str(alt + 1)
