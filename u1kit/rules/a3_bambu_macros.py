"""A3: Detect Bambu AMS macros in G-code fields."""

from __future__ import annotations

import re

from u1kit.rules.base import Context, Result, Rule, Severity

# G-code config keys to scan
GCODE_FIELDS = (
    "machine_start_gcode",
    "machine_end_gcode",
    "change_filament_gcode",
    "layer_change_gcode",
)

# Patterns that indicate Bambu AMS syntax
BAMBU_PATTERNS = [
    re.compile(r"\bM620\b"),
    re.compile(r"\bM621\b"),
    re.compile(r"\bM623\b"),
    re.compile(r"\bAMS\b", re.IGNORECASE),
]


class A3BambuMacros(Rule):
    """Detect Bambu M620/M621/M623/AMS macros in G-code fields."""

    @property
    def id(self) -> str:
        return "A3"

    @property
    def name(self) -> str:
        return "Bambu AMS macros"

    def check(self, context: Context) -> list[Result]:
        config = context.config
        findings: list[str] = []

        for field_name in GCODE_FIELDS:
            value = config.get(field_name, "")
            if not isinstance(value, str):
                continue
            for pattern in BAMBU_PATTERNS:
                if pattern.search(value):
                    findings.append(f"{field_name}: contains {pattern.pattern}")

        if not findings:
            return []

        diff = "\n".join(findings)
        return [
            Result(
                rule_id=self.id,
                severity=Severity.FAIL,
                message=f"Bambu AMS macros found in G-code fields:\n{diff}",
                fixer_id="a3",
                diff_preview=diff,
            )
        ]
