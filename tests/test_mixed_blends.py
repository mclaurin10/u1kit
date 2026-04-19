"""Tests for the mixed_filament_definitions parser."""

from __future__ import annotations

from u1kit.mixed_blends import MixedBlend, parse_mixed_definitions


class TestParseMixedDefinitions:
    """Parse semicolon-separated CSV blend definitions."""

    def test_empty_string_returns_empty(self) -> None:
        assert parse_mixed_definitions("") == []

    def test_whitespace_only_returns_empty(self) -> None:
        assert parse_mixed_definitions("   ") == []

    def test_single_blend(self) -> None:
        raw = "1,2,0,1,50,0,5,0,0,0,0,0"
        blends = parse_mixed_definitions(raw)
        assert len(blends) == 1
        blend = blends[0]
        assert blend.filament_a == 1
        assert blend.filament_b == 2
        assert blend.ratio_percent == 50
        assert blend.raw_fields == (
            "1", "2", "0", "1", "50", "0", "5", "0", "0", "0", "0", "0",
        )

    def test_multiple_blends(self) -> None:
        raw = "1,2,0,1,50,0,5,0,0,0,0,0;1,3,0,1,33,0,5,0,0,0,0,0"
        blends = parse_mixed_definitions(raw)
        assert len(blends) == 2
        assert blends[0].ratio_percent == 50
        assert blends[1].ratio_percent == 33
        assert blends[1].filament_b == 3

    def test_skips_short_entries(self) -> None:
        raw = "1,2,0;1,2,0,1,50,0,5,0,0,0,0,0"
        blends = parse_mixed_definitions(raw)
        assert len(blends) == 1
        assert blends[0].ratio_percent == 50

    def test_skips_invalid_ratio(self) -> None:
        raw = "1,2,0,1,abc,0,5,0,0,0,0,0"
        assert parse_mixed_definitions(raw) == []

    def test_skips_invalid_filament_a(self) -> None:
        raw = "xx,2,0,1,50,0,5,0,0,0,0,0"
        assert parse_mixed_definitions(raw) == []

    def test_skips_invalid_filament_b(self) -> None:
        raw = "1,yy,0,1,50,0,5,0,0,0,0,0"
        assert parse_mixed_definitions(raw) == []

    def test_skips_empty_entries_between_semicolons(self) -> None:
        raw = "1,2,0,1,50,0,5,0,0,0,0,0;;1,3,0,1,33,0,5,0,0,0,0,0"
        blends = parse_mixed_definitions(raw)
        assert len(blends) == 2

    def test_preserves_all_raw_fields_beyond_typed_ones(self) -> None:
        raw = "1,2,a,b,50,c,5,d,e,f,g,h"
        blends = parse_mixed_definitions(raw)
        assert len(blends) == 1
        assert blends[0].raw_fields[5] == "c"
        assert blends[0].raw_fields[11] == "h"

    def test_mixed_blend_is_frozen(self) -> None:
        blend = MixedBlend(
            filament_a=1,
            filament_b=2,
            ratio_percent=50,
            raw_fields=("1", "2", "0", "1", "50"),
        )
        try:
            blend.filament_a = 9  # type: ignore[misc]
        except Exception:
            return
        raise AssertionError("MixedBlend should be frozen")
