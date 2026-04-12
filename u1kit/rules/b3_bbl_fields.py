"""B3: Remove Bambu-specific filament fields."""

from __future__ import annotations

from u1kit.bbl import is_u1_compatible, normalize_compatible_printers
from u1kit.rules.base import Context, Result, Rule, Severity

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
        if isinstance(inherits, str) and inherits and not is_u1_compatible(inherits):
            found.append(f"config: inherits={inherits!r} (non-U1 profile chain)")

        # Check compatible_printers for non-U1 entries
        compatible = config.get("compatible_printers", [])
        if isinstance(compatible, (str, list)):
            printers = normalize_compatible_printers(compatible)
            non_u1 = [p for p in printers if not is_u1_compatible(p)]
            if non_u1:
                found.append(f"config: compatible_printers contains non-U1: {non_u1}")

        # Check filament-level BBL fields
        for path, fil_config in context.filament_configs.items():
            for field_name in BBL_FIELDS:
                if field_name in fil_config:
                    val = fil_config[field_name]
                    if field_name == "inherits" and isinstance(val, str):
                        if val and not is_u1_compatible(val):
                            found.append(f"{path}: {field_name}={val!r}")
                    elif field_name == "compatible_printers":
                        if isinstance(val, (str, list)):
                            printers_f = normalize_compatible_printers(val)
                            non_u1_f = [p for p in printers_f if not is_u1_compatible(p)]
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
