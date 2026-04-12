"""Tests for the B1 filament-merge fixer."""

from __future__ import annotations

import copy
from typing import Any

import click
import pytest

from u1kit.fixers.b1_filament_count import (
    B1FilamentCountFixer,
    B1MergeRequiresConsent,
)
from u1kit.interactive import FixAction
from u1kit.rules.base import Context


def _five_filament_config() -> dict[str, Any]:
    # Two nearly-identical reds (indices 0, 1) should be the closest pair.
    return {
        "filament_colour": ["#FF0000", "#FE0000", "#00FF00", "#0000FF", "#FFFF00"],
        "filament_type": ["PLA", "PLA", "PLA", "PLA", "PLA"],
        "filament_settings_id": ["A", "B", "C", "D", "E"],
        "filament_max_volumetric_speed": ["20", "20", "20", "20", "20"],
        "wall_filament": "1",
        "sparse_infill_filament": "2",
        "support_filament": "3",
    }


class TestB1Fixer:
    def test_merges_closest_pair_with_force(self) -> None:
        config = _five_filament_config()
        ctx = Context(config=config, options={"b1_force_merge": True})
        B1FilamentCountFixer().apply(config, {}, ctx)

        assert len(config["filament_colour"]) == 4
        # Closest pair is index 0 (#FF0000) and 1 (#FE0000). Index 1 is popped.
        assert config["filament_colour"][0] == "#FF0000"
        # wall_filament pointed at 1 (idx 0) — still valid.
        assert config["wall_filament"] == "1"
        # sparse_infill_filament pointed at 2 (idx 1) — remapped to 1 (idx 0).
        assert config["sparse_infill_filament"] == "1"
        # support_filament pointed at 3 (idx 2) — shifted down to 2.
        assert config["support_filament"] == "2"
        # Parallel arrays all shrink together.
        assert len(config["filament_type"]) == 4
        assert len(config["filament_settings_id"]) == 4
        assert len(config["filament_max_volumetric_speed"]) == 4
        assert config["filament_settings_id"] == ["A", "C", "D", "E"]

    def test_refuses_without_force_or_interactive(self) -> None:
        config = _five_filament_config()
        ctx = Context(config=config)
        with pytest.raises(B1MergeRequiresConsent):
            B1FilamentCountFixer().apply(config, {}, ctx)

    def test_already_at_four_is_noop(self) -> None:
        config: dict[str, Any] = {
            "filament_colour": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"],
            "filament_type": ["PLA", "PLA", "PLA", "PLA"],
        }
        snapshot = copy.deepcopy(config)
        # No consent needed — nothing to merge.
        B1FilamentCountFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_idempotent_after_reduction(self) -> None:
        config = _five_filament_config()
        ctx = Context(config=config, options={"b1_force_merge": True})
        B1FilamentCountFixer().apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        # Second call is a no-op (count already at 4).
        B1FilamentCountFixer().apply(config, {}, Context(config=config))
        assert config == snapshot

    def test_reduces_seven_to_four(self) -> None:
        config: dict[str, Any] = {
            "filament_colour": [
                "#FF0000",
                "#FE0000",
                "#00FF00",
                "#00FE00",
                "#0000FF",
                "#0000FE",
                "#FFFF00",
            ],
            "filament_type": ["PLA"] * 7,
            "wall_filament": "1",
        }
        ctx = Context(config=config, options={"b1_force_merge": True})
        B1FilamentCountFixer().apply(config, {}, ctx)
        assert len(config["filament_colour"]) == 4

    def test_interactive_apply_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "u1kit.fixers.b1_filament_count.prompt_fix",
            lambda *a, **k: FixAction.APPLY,
        )
        config = _five_filament_config()
        ctx = Context(config=config, options={"b1_interactive": True})
        B1FilamentCountFixer().apply(config, {}, ctx)
        assert len(config["filament_colour"]) == 4

    def test_interactive_skip_all_stops(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "u1kit.fixers.b1_filament_count.prompt_fix",
            lambda *a, **k: FixAction.SKIP,
        )
        config = _five_filament_config()
        ctx = Context(config=config, options={"b1_interactive": True})
        B1FilamentCountFixer().apply(config, {}, ctx)
        # User skipped every possible merge — nothing applied.
        assert len(config["filament_colour"]) == 5

    def test_interactive_quit_aborts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "u1kit.fixers.b1_filament_count.prompt_fix",
            lambda *a, **k: FixAction.QUIT,
        )
        config = _five_filament_config()
        ctx = Context(config=config, options={"b1_interactive": True})
        with pytest.raises(click.Abort):
            B1FilamentCountFixer().apply(config, {}, ctx)

    def test_semicolon_string_colours_supported(self) -> None:
        # Phase 1 synthetic shape: filament_colour as semicolon-separated string.
        config: dict[str, Any] = {
            "filament_colour": "#FF0000;#FE0000;#00FF00;#0000FF;#FFFF00",
            "filament_type": "PLA;PLA;PLA;PLA;PLA",
        }
        ctx = Context(config=config, options={"b1_force_merge": True})
        B1FilamentCountFixer().apply(config, {}, ctx)
        # After merge the list representation is lists; count is 4.
        from u1kit.filaments import get_filament_count

        assert get_filament_count(config) == 4


class TestB1PipelineIntegration:
    def test_auto_mode_records_refusal_without_crash(self) -> None:
        from u1kit.fixers import get_fixer_map
        from u1kit.fixers.base import FixMode, Pipeline
        from u1kit.rules.b1_filament_count import B1FilamentCount

        config = _five_filament_config()
        pipeline = Pipeline(
            rules=[B1FilamentCount],
            fixers=get_fixer_map(),
            mode=FixMode.AUTO,
        )
        results, fixer_results, _, _ = pipeline.run(config, {})

        assert len(results) == 1
        assert results[0].fixer_id == "b1"
        # Pipeline did not crash; it recorded the refusal.
        assert len(fixer_results) == 1
        assert fixer_results[0].applied is False
        assert "refus" in fixer_results[0].message.lower()
        # Config is unchanged.
        assert len(config["filament_colour"]) == 5
