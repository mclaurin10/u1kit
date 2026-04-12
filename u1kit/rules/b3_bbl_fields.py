"""B3: Remove Bambu-specific filament fields."""

from __future__ import annotations

import re

from u1kit.rules.base import Context, Result, Rule, Severity

_U1_RE = re.compile(r"\bU1\b", re.IGNORECASE)

# Fields that are Bambu-specific and should be removed for U1
BBL_FIELDS = (
    "filament_extruder_variant",
    "compatible_printers",
    "inherits",
)

# Bambu-specific top-level fields
BBL_TOP_LEVEL_FIELDS = (
    "bbl_use_printhost",
    "bbl_calib_mark_logo",
)


class B3BblFields(Rule):
    """Detect Bambu-specific fields that should be removed."""

    @property
    def id(self) -> str:
        return "B3"

    @property
    def name(self) -> str:
        return "BBL-specific fields"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        found: list[str] = []

        # Check top-level BBL fields
        for field_name in BBL_TOP_LEVEL_FIELDS:
            if field_name in config:
                found.append(f"config: {field_name}")

        # Check inherits chains pointing to non-U1 profiles
        inherits = config.get("inherits", "")
        if isinstance(inherits, str) and inherits and not _U1_RE.search(inherits):
            found.append(f"config: inherits={inherits!r} (non-U1 profile chain)")

        # Check compatible_printers for non-U1 entries
        compatible = config.get("compatible_printers", [])
        if isinstance(compatible, str):
            compatible = [p.strip() for p in compatible.split(";") if p.strip()]
        if isinstance(compatible, list):
            non_u1 = [p for p in compatible if not _U1_RE.search(p)]
            if non_u1:
                found.append(f"config: compatible_printers contains non-U1: {non_u1}")

        # Check filament-level BBL fields
        for path, fil_config in context.filament_configs.items():
            for field_name in BBL_FIELDS:
                if field_name in fil_config:
                    val = fil_config[field_name]
                    if field_name == "inherits" and isinstance(val, str):
                        if val and not _U1_RE.search(val):
                            found.append(f"{path}: {field_name}={val!r}")
                    elif field_name == "compatible_printers":
                        if isinstance(val, str):
                            val = [p.strip() for p in val.split(";") if p.strip()]
                        if isinstance(val, list):
                            non_u1_f = [p for p in val if not _U1_RE.search(p)]
                            if non_u1_f:
                                found.append(f"{path}: compatible_printers non-U1: {non_u1_f}")
                    else:
                        found.append(f"{path}: {field_name}")

        if not found:
            return []

        diff = "\n".join(found)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.WARN,
                message=f"Bambu-specific fields found:\n{diff}",
                fixer_id="b3",
                diff_preview=diff,
            )
        ]
