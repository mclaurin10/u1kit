"""A1: Detect source slicer. Info-only, gates downstream rules."""

from __future__ import annotations

from u1kit.rules.base import Context, Result, Rule, Severity

# Keys that indicate Full Spectrum (Snapmaker) origin
FULL_SPECTRUM_KEYS = (
    "mixed_filament_height_lower_bound",
    "mixed_filament_height_upper_bound",
    "mixed_filament_height_layer_height",
)


class A1SourceSlicer(Rule):
    """Detect source slicer by inspecting config keys."""

    @property
    def id(self) -> str:
        return "A1"

    @property
    def name(self) -> str:
        return "Source slicer detection"

    def check(self, context: Context) -> list[Result]:
        config = context.config

        # Check for Full Spectrum keys
        has_fs_keys = any(k in config for k in FULL_SPECTRUM_KEYS)
        if has_fs_keys:
            context.source_slicer = "full_spectrum"
            return [
                Result(
                    rule_id=self.id,
                    severity=Severity.INFO,
                    message="Source: Full Spectrum (Snapmaker Orca) — "
                    "mixed_filament_height keys present.",
                )
            ]

        # Check for Bambu indicators
        printer_model = config.get("printer_model", "")
        printer_settings_id = config.get("printer_settings_id", "")

        bambu_indicators = [
            "Bambu" in printer_model,
            "Bambu" in printer_settings_id,
            "BBL" in printer_settings_id,
            config.get("bbl_use_printhost", "") != "",
        ]

        if any(bambu_indicators):
            context.source_slicer = "bambu"
            return [
                Result(
                    rule_id=self.id,
                    severity=Severity.INFO,
                    message=f"Source: Bambu Lab slicer "
                    f"(printer_model={printer_model!r}, "
                    f"printer_settings_id={printer_settings_id!r}).",
                )
            ]

        context.source_slicer = "unknown"
        return [
            Result(
                rule_id=self.id,
                severity=Severity.INFO,
                message="Source: Unknown slicer — no Bambu or Full Spectrum markers detected.",
            )
        ]
