"""Parallel-array accessor for per-filament fields on project_settings.config.

Snapmaker Orca native U1 exports store per-filament data as flat parallel lists
keyed on `filament_colour`'s length. Selectors like `wall_filament` are scalar
1-based indices into those lists. This module centralizes reading and
classifying those fields so individual rules/fixers do not re-parse the shape.

Phase 1's Bambu-shaped synthetic fixtures sometimes store `filament_colour` as a
semicolon-separated string; both shapes are handled.
"""

from __future__ import annotations

from typing import Any

FLEXIBLE_TYPES = frozenset({"TPU", "PEBA", "TPE"})
RIGID_PREFERRED: tuple[str, ...] = ("PLA", "PETG", "ABS", "ASA", "PC")

SELECTOR_FIELDS: tuple[str, ...] = (
    "wall_filament",
    "sparse_infill_filament",
    "solid_infill_filament",
    "support_filament",
    "support_interface_filament",
    "wipe_tower_filament",
)


def _as_list(value: Any) -> list[str] | None:
    """Normalize a field that may be a list or a semicolon-separated string.

    Returns None if the value is not list-shaped (e.g. plain scalar).
    """
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and ";" in value:
        return [part for part in value.split(";") if part]
    return None


def get_filament_count(config: dict[str, Any]) -> int:
    """Return the number of filament slots.

    Uses `filament_colour` length. Accepts either the native list shape or a
    semicolon-separated string (legacy Bambu fixtures).
    """
    colours = _as_list(config.get("filament_colour"))
    if colours is None:
        return 0
    return len(colours)


def get_filament_field(
    config: dict[str, Any], field: str, index: int
) -> str | None:
    """Return the value at slot `index` for a parallel-array field.

    If the field stores a list (or semicolon-separated string), return the
    element at `index` or None when out of range. If the field is a true
    scalar, return it only at index 0.
    """
    if index < 0:
        return None

    raw = config.get(field)
    if raw is None:
        return None

    as_list = _as_list(raw)
    if as_list is not None:
        if index >= len(as_list):
            return None
        return as_list[index]

    # True scalar.
    if index == 0:
        return str(raw)
    return None


def parse_scalar_index(value: Any) -> int | None:
    """Parse a scalar filament selector to a 0-based index.

    `'1'`, `1` → 0 (first filament).
    `'0'`, `0`, `''`, `None`, or unparseable → None (meaning 'unset').
    """
    if value is None:
        return None
    try:
        n = int(str(value).strip() or "0")
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    return n - 1


def get_used_filament_indices(config: dict[str, Any]) -> list[int]:
    """Return the 0-based indices of filaments referenced by wall/support/
    infill/wipe-tower selectors.

    Deduplicated and sorted. Unset selectors (`'0'`, empty) are ignored.
    If no selectors are present at all, falls back to treating every slot as
    used (Phase 1 synthetic fixtures often omit the selector fields).
    """
    count = get_filament_count(config)
    if count == 0:
        return []

    indices: set[int] = set()
    any_selector_present = False
    for field in SELECTOR_FIELDS:
        if field not in config:
            continue
        any_selector_present = True
        idx = parse_scalar_index(config[field])
        if idx is not None and 0 <= idx < count:
            indices.add(idx)

    if not any_selector_present:
        return list(range(count))

    return sorted(indices)


def is_flexible(filament_type: str | None) -> bool:
    """True if `filament_type` is in FLEXIBLE_TYPES (case-insensitive)."""
    if not filament_type:
        return False
    return filament_type.strip().upper() in FLEXIBLE_TYPES


def broadcast_field(
    config: dict[str, Any],
    field: str,
    count: int,
    default: str,
) -> list[str]:
    """Return the value of `field` as a parallel array of length `count`.

    Used by rules like B4 that need to inject per-filament values into a
    field that may currently be a scalar. Behaviour:

    - Missing/None → ``[default] * count``
    - List of length ``count`` → returned as a new list
    - Longer list → truncated to ``count``
    - Shorter list → padded with the last element (or ``default`` if empty)
    - Scalar → broadcast to every slot
    - Semicolon-string → split, then handled as a list
    """
    raw = config.get(field)
    if raw is None:
        return [default] * count

    as_list = _as_list(raw)
    if as_list is not None:
        if len(as_list) == count:
            return list(as_list)
        if len(as_list) > count:
            return list(as_list[:count])
        pad = as_list[-1] if as_list else default
        return list(as_list) + [pad] * (count - len(as_list))

    return [str(raw)] * count


def pop_filament_slot(
    config: dict[str, Any],
    slot_index: int,
    *,
    target_index: int | None = None,
) -> None:
    """Remove filament slot `slot_index` from every parallel array and remap
    scalar selectors in-place.

    Every config value whose length matches the current filament count is
    treated as a parallel array; the element at `slot_index` is popped.
    Scalar selector fields (`wall_filament` etc.) pointing at `slot_index + 1`
    are redirected to `target_index + 1` (if given) or cleared to `'0'`.
    Higher-indexed selectors are decremented by one to preserve meaning.

    `target_index` must be < `slot_index` (caller's responsibility: used by
    B1's merge, which always merges the higher-index filament into the lower).
    """
    count = get_filament_count(config)
    if count == 0 or slot_index < 0 or slot_index >= count:
        return

    for key in list(config.keys()):
        as_list = _as_list(config[key])
        if as_list is None or len(as_list) != count:
            continue
        config[key] = as_list[:slot_index] + as_list[slot_index + 1 :]

    for field in SELECTOR_FIELDS:
        raw = config.get(field)
        if raw is None:
            continue
        try:
            idx_1b = int(str(raw).strip() or "0")
        except (TypeError, ValueError):
            continue
        if idx_1b <= 0:
            continue
        if idx_1b == slot_index + 1:
            config[field] = (
                str(target_index + 1) if target_index is not None else "0"
            )
        elif idx_1b > slot_index + 1:
            config[field] = str(idx_1b - 1)


def find_rigid_alternative(
    config: dict[str, Any], exclude_index: int
) -> int | None:
    """Return the 0-based index of a non-flexible filament other than
    `exclude_index`.

    Prefers filaments in `RIGID_PREFERRED` order (PLA first, then PETG, etc.).
    Returns None if no rigid alternative exists.
    """
    count = get_filament_count(config)
    if count == 0:
        return None

    candidates: list[tuple[int, int]] = []  # (preferred_rank, slot_index)
    for i in range(count):
        if i == exclude_index:
            continue
        ftype = get_filament_field(config, "filament_type", i)
        if ftype is None or is_flexible(ftype):
            continue
        upper = ftype.strip().upper()
        try:
            rank = RIGID_PREFERRED.index(upper)
        except ValueError:
            rank = len(RIGID_PREFERRED)  # non-preferred rigid — lowest priority
        candidates.append((rank, i))

    if not candidates:
        return None
    candidates.sort(key=lambda pair: (pair[0], pair[1]))
    return candidates[0][1]
