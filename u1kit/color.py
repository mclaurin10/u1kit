"""Perceptual color distance for Phase 2 rule B1 (filament merge).

Pure stdlib (math only). Implements sRGB → CIE Lab → CIEDE2000 per Sharma,
Wu, and Dalal (2005). The module is used by ``fixers/b1_filament_count.py``
to pick which filament pair to merge first.
"""

from __future__ import annotations

import math

Lab = tuple[float, float, float]
Rgb = tuple[float, float, float]

_D65_WHITE: Lab = (95.047, 100.000, 108.883)
_EPSILON = 216.0 / 24389.0  # (6/29)^3, CIE Lab f-function break
_KAPPA = 24389.0 / 27.0  # (29/3)^3


def hex_to_rgb(hex_str: str) -> Rgb:
    """Parse ``#RRGGBB`` / ``RRGGBB`` / ``#RGB`` into 0-255 float channels."""
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"invalid hex color: {hex_str!r}")
    return (
        float(int(s[0:2], 16)),
        float(int(s[2:4], 16)),
        float(int(s[4:6], 16)),
    )


def _srgb_to_linear(c: float) -> float:
    c /= 255.0
    if c <= 0.04045:
        return c / 12.92
    return float(((c + 0.055) / 1.055) ** 2.4)


def rgb_to_lab(rgb: Rgb) -> Lab:
    """Convert sRGB (0-255 per channel) to CIE Lab under D65 reference white."""
    r, g, b = (_srgb_to_linear(c) for c in rgb)

    # sRGB D65 → XYZ (IEC 61966-2-1), scaled ×100 to match reference white.
    x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) * 100.0
    y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) * 100.0
    z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) * 100.0

    xn, yn, zn = _D65_WHITE
    fx = _lab_f(x / xn)
    fy = _lab_f(y / yn)
    fz = _lab_f(z / zn)

    return (116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz))


def _lab_f(t: float) -> float:
    if t > _EPSILON:
        return float(t ** (1.0 / 3.0))
    return (_KAPPA * t + 16.0) / 116.0


def ciede2000(lab1: Lab, lab2: Lab) -> float:
    """Return the CIEDE2000 perceptual color difference between two Lab triples.

    Verified against the 34 reference pairs in Sharma, Wu, and Dalal (2005)
    to within ±1e-4. ``kL = kC = kH = 1`` (unweighted).
    """
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2

    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2.0

    c_bar_pow7 = c_bar**7
    g = 0.5 * (1.0 - math.sqrt(c_bar_pow7 / (c_bar_pow7 + 25.0**7)))

    a1_prime = (1.0 + g) * a1
    a2_prime = (1.0 + g) * a2
    c1_prime = math.hypot(a1_prime, b1)
    c2_prime = math.hypot(a2_prime, b2)

    h1_prime = _hue_degrees(b1, a1_prime)
    h2_prime = _hue_degrees(b2, a2_prime)

    dl_prime = l2 - l1
    dc_prime = c2_prime - c1_prime

    if c1_prime * c2_prime == 0.0:
        dh_prime = 0.0
    else:
        diff = h2_prime - h1_prime
        if diff > 180.0:
            diff -= 360.0
        elif diff < -180.0:
            diff += 360.0
        dh_prime = diff

    big_dh_prime = (
        2.0 * math.sqrt(c1_prime * c2_prime) * math.sin(math.radians(dh_prime / 2.0))
    )

    l_bar_prime = (l1 + l2) / 2.0
    c_bar_prime = (c1_prime + c2_prime) / 2.0

    if c1_prime * c2_prime == 0.0:
        h_bar_prime = h1_prime + h2_prime
    else:
        total = h1_prime + h2_prime
        if abs(h1_prime - h2_prime) > 180.0:
            total += 360.0 if total < 360.0 else -360.0
        h_bar_prime = total / 2.0

    t = (
        1.0
        - 0.17 * math.cos(math.radians(h_bar_prime - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * h_bar_prime))
        + 0.32 * math.cos(math.radians(3.0 * h_bar_prime + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * h_bar_prime - 63.0))
    )

    d_theta = 30.0 * math.exp(-(((h_bar_prime - 275.0) / 25.0) ** 2))

    c_bar_prime_pow7 = c_bar_prime**7
    r_c = 2.0 * math.sqrt(c_bar_prime_pow7 / (c_bar_prime_pow7 + 25.0**7))

    s_l = 1.0 + (0.015 * (l_bar_prime - 50.0) ** 2) / math.sqrt(
        20.0 + (l_bar_prime - 50.0) ** 2
    )
    s_c = 1.0 + 0.045 * c_bar_prime
    s_h = 1.0 + 0.015 * c_bar_prime * t

    r_t = -math.sin(math.radians(2.0 * d_theta)) * r_c

    term_l = dl_prime / s_l
    term_c = dc_prime / s_c
    term_h = big_dh_prime / s_h

    return math.sqrt(term_l**2 + term_c**2 + term_h**2 + r_t * term_c * term_h)


def _hue_degrees(b: float, a_prime: float) -> float:
    if b == 0.0 and a_prime == 0.0:
        return 0.0
    h = math.degrees(math.atan2(b, a_prime))
    if h < 0.0:
        h += 360.0
    return h


def hex_distance(hex_a: str, hex_b: str) -> float:
    """Shortcut: CIEDE2000 distance between two ``#RRGGBB`` color strings."""
    return ciede2000(rgb_to_lab(hex_to_rgb(hex_a)), rgb_to_lab(hex_to_rgb(hex_b)))
