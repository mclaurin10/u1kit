"""Tests for u1kit.bbl shared utilities."""

from __future__ import annotations

from u1kit.bbl import filter_u1_printers, is_u1_compatible, normalize_compatible_printers


class TestIsU1Compatible:
    def test_positive(self) -> None:
        assert is_u1_compatible("Snapmaker U1")
        assert is_u1_compatible("Snapmaker U1 0.4 nozzle")
        assert is_u1_compatible("u1")  # case-insensitive

    def test_negative(self) -> None:
        assert not is_u1_compatible("Bambu Lab X1 Carbon")
        assert not is_u1_compatible("U1Megatron")  # no word boundary
        assert not is_u1_compatible("")


class TestNormalizeCompatiblePrinters:
    def test_semicolon_string(self) -> None:
        result = normalize_compatible_printers("Bambu Lab X1;Snapmaker U1")
        assert result == ["Bambu Lab X1", "Snapmaker U1"]

    def test_semicolon_with_whitespace(self) -> None:
        result = normalize_compatible_printers(" Bambu Lab X1 ; Snapmaker U1 ; ")
        assert result == ["Bambu Lab X1", "Snapmaker U1"]

    def test_list_passthrough(self) -> None:
        original = ["Bambu Lab X1", "Snapmaker U1"]
        result = normalize_compatible_printers(original)
        assert result == original
        assert result is not original  # returns a copy


class TestFilterU1Printers:
    def test_mixed_list(self) -> None:
        result = filter_u1_printers(["Bambu Lab X1", "Snapmaker U1", "Other U1 variant"])
        assert result == ["Snapmaker U1", "Other U1 variant"]

    def test_semicolon_input(self) -> None:
        result = filter_u1_printers("Bambu Lab X1;Snapmaker U1")
        assert result == ["Snapmaker U1"]

    def test_no_u1_entries(self) -> None:
        result = filter_u1_printers(["Bambu Lab X1"])
        assert result == []
