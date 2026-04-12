"""Tests for u1kit.color: CIEDE2000 color distance.

Reference values from Sharma, Wu, and Dalal (2005), "The CIEDE2000 color-
difference formula: Implementation notes, supplementary test data, and
mathematical observations" — the canonical 34-pair verification table.
"""

from __future__ import annotations

import pytest

from u1kit.color import ciede2000, hex_distance, hex_to_rgb, rgb_to_lab

SHARMA_PAIRS: list[tuple[tuple[float, float, float], tuple[float, float, float], float]] = [
    ((50.0000, 2.6772, -79.7751), (50.0000, 0.0000, -82.7485), 2.0425),
    ((50.0000, 3.1571, -77.2803), (50.0000, 0.0000, -82.7485), 2.8615),
    ((50.0000, 2.8361, -74.0200), (50.0000, 0.0000, -82.7485), 3.4412),
    ((50.0000, -1.3802, -84.2814), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, -1.1848, -84.8006), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, -0.9009, -85.5211), (50.0000, 0.0000, -82.7485), 1.0000),
    ((50.0000, 0.0000, 0.0000), (50.0000, -1.0000, 2.0000), 2.3669),
    ((50.0000, -1.0000, 2.0000), (50.0000, 0.0000, 0.0000), 2.3669),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0009), 7.1792),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0010), 7.1792),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0011), 7.2195),
    ((50.0000, 2.4900, -0.0010), (50.0000, -2.4900, 0.0012), 7.2195),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0009, -2.4900), 4.8045),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0010, -2.4900), 4.8045),
    ((50.0000, -0.0010, 2.4900), (50.0000, 0.0011, -2.4900), 4.7461),
    ((50.0000, 2.5000, 0.0000), (50.0000, 0.0000, -2.5000), 4.3065),
    ((50.0000, 2.5000, 0.0000), (73.0000, 25.0000, -18.0000), 27.1492),
    ((50.0000, 2.5000, 0.0000), (61.0000, -5.0000, 29.0000), 22.8977),
    ((50.0000, 2.5000, 0.0000), (56.0000, -27.0000, -3.0000), 31.9030),
    ((50.0000, 2.5000, 0.0000), (58.0000, 24.0000, 15.0000), 19.4535),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.1736, 0.5854), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.2972, 0.0000), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 1.8634, 0.5757), 1.0000),
    ((50.0000, 2.5000, 0.0000), (50.0000, 3.2592, 0.3350), 1.0000),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
    ((63.0109, -31.0961, -5.8663), (62.8187, -29.7946, -4.0864), 1.2630),
    ((61.2901, 3.7196, -5.3901), (61.4292, 2.2480, -4.9620), 1.8731),
    ((35.0831, -44.1164, 3.7933), (35.0232, -40.0716, 1.5901), 1.8645),
    ((22.7233, 20.0904, -46.6940), (23.0331, 14.9730, -42.5619), 2.0373),
    ((36.4612, 47.8580, 18.3852), (36.2715, 50.5065, 21.2231), 1.4146),
    ((90.8027, -2.0831, 1.4410), (91.1528, -1.6435, 0.0447), 1.4441),
    ((90.9257, -0.5406, -0.9208), (88.6381, -0.8985, -0.7239), 1.5381),
    ((6.7747, -0.2908, -2.4247), (5.8714, -0.0985, -2.2286), 0.6377),
    ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082),
]


class TestCiede2000Sharma:
    @pytest.mark.parametrize("lab1,lab2,expected", SHARMA_PAIRS)
    def test_matches_sharma_reference(
        self,
        lab1: tuple[float, float, float],
        lab2: tuple[float, float, float],
        expected: float,
    ) -> None:
        assert ciede2000(lab1, lab2) == pytest.approx(expected, abs=1e-4)

    def test_symmetric(self) -> None:
        lab1 = (60.0, 20.0, -30.0)
        lab2 = (40.0, -10.0, 15.0)
        assert ciede2000(lab1, lab2) == pytest.approx(ciede2000(lab2, lab1), abs=1e-9)

    def test_identical_is_zero(self) -> None:
        lab = (50.0, 10.0, -20.0)
        assert ciede2000(lab, lab) == pytest.approx(0.0, abs=1e-9)


class TestHexToRgb:
    def test_long_form(self) -> None:
        assert hex_to_rgb("#003776") == (0.0, 55.0, 118.0)

    def test_no_hash(self) -> None:
        assert hex_to_rgb("FF0000") == (255.0, 0.0, 0.0)

    def test_lowercase(self) -> None:
        assert hex_to_rgb("#00ff00") == (0.0, 255.0, 0.0)

    def test_short_form(self) -> None:
        assert hex_to_rgb("#f00") == (255.0, 0.0, 0.0)


class TestRgbToLab:
    def test_white(self) -> None:
        lab = rgb_to_lab((255.0, 255.0, 255.0))
        assert lab[0] == pytest.approx(100.0, abs=1e-2)
        assert lab[1] == pytest.approx(0.0, abs=1e-2)
        assert lab[2] == pytest.approx(0.0, abs=1e-2)

    def test_black(self) -> None:
        lab = rgb_to_lab((0.0, 0.0, 0.0))
        assert lab[0] == pytest.approx(0.0, abs=1e-6)
        assert lab[1] == pytest.approx(0.0, abs=1e-6)
        assert lab[2] == pytest.approx(0.0, abs=1e-6)

    def test_red_lightness_in_range(self) -> None:
        lightness, _a, _b = rgb_to_lab((255.0, 0.0, 0.0))
        # Pure sRGB red → L ≈ 53.24
        assert 50.0 < lightness < 55.0


class TestHexDistance:
    def test_identical_is_zero(self) -> None:
        assert hex_distance("#FF0000", "#FF0000") == pytest.approx(0.0, abs=1e-6)

    def test_red_vs_green_large(self) -> None:
        # Pure red vs pure green: perceptually very different.
        assert hex_distance("#FF0000", "#00FF00") > 70.0

    def test_similar_reds_small(self) -> None:
        # Tiny hex difference → small CIEDE2000.
        assert hex_distance("#FF0000", "#FE0000") < 1.0

    def test_symmetric(self) -> None:
        a = hex_distance("#003776", "#2D9E59")
        b = hex_distance("#2D9E59", "#003776")
        assert a == pytest.approx(b, abs=1e-9)
