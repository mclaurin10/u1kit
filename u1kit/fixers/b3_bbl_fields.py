"""B3 fixer: Remove Bambu-specific fields."""

from __future__ import annotations

import re
from typing import Any

from u1kit.fixers.base import Fixer
from u1kit.rules.base import Context

_U1_RE = re.compile(r"\bU1\b", re.IGNORECASE)

BBL_TOP_LEVEL_FIELDS = (
    "bbl_use_printhost",
    "bbl_calib_mark_logo",
)


class B3BblFieldsFixer(Fixer):
    """Remove Bambu-specific fields from config and filament configs."""

    @property
    def id(self) -> str:
        return "b3"

    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        # Remove top-level BBL fields
        for field_name in BBL_TOP_LEVEL_FIELDS:
            config.pop(field_name, None)

        # Remove inherits if it points to a non-U1 profile
        inherits = config.get("inherits", "")
        if isinstance(inherits, str) and inherits and not _U1_RE.search(inherits):
            del config["inherits"]

        # Clean compatible_printers — keep only U1 entries
        compatible = config.get("compatible_printers", [])
        if isinstance(compatible, str):
            compatible = [p.strip() for p in compatible.split(";") if p.strip()]
        if isinstance(compatible, list):
            u1_only = [p for p in compatible if _U1_RE.search(p)]
            if len(u1_only) != len(compatible):
                if u1_only:
                    config["compatible_printers"] = u1_only
                else:
                    config.pop("compatible_printers", None)

        # Clean filament configs
        for _path, fil_config in filament_configs.items():
            fil_config.pop("filament_extruder_variant", None)

            fil_inherits = fil_config.get("inherits", "")
            if isinstance(fil_inherits, str) and fil_inherits and not _U1_RE.search(fil_inherits):
                del fil_config["inherits"]

            fil_compat = fil_config.get("compatible_printers", [])
            if isinstance(fil_compat, str):
                fil_compat = [p.strip() for p in fil_compat.split(";") if p.strip()]
            if isinstance(fil_compat, list):
                u1_fil = [p for p in fil_compat if _U1_RE.search(p)]
                if len(u1_fil) != len(fil_compat):
                    if u1_fil:
                        fil_config["compatible_printers"] = u1_fil
                    else:
                        fil_config.pop("compatible_printers", None)
