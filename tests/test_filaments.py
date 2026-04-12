"""Tests for the u1kit.filaments parallel-array accessor."""

from __future__ import annotations

import pytest

from u1kit.filaments import (
    find_rigid_alternative,
    get_filament_count,
    get_filament_field,
    get_used_filament_indices,
    is_flexible,
    parse_scalar_index,
    pop_filament_slot,
)


class TestGetFilamentCount:
    def test_from_list(self) -> None:
        config = {"filament_colour": ["#000", "#111", "#222", "#333"]}
        assert get_filament_count(config) == 4

    def test_from_semicolon_string(self) -> None:
        config = {"filament_colour": "#FF0000;#00FF00;#0000FF;#FFFF00"}
        assert get_filament_count(config) == 4

    def test_absent_returns_zero(self) -> None:
        assert get_filament_count({}) == 0

    def test_empty_list(self) -> None:
        assert get_filament_count({"filament_colour": []}) == 0


class TestGetFilamentField:
    def test_list_field(self) -> None:
        config = {"filament_type": ["PLA", "TPU", "PETG"]}
        assert get_filament_field(config, "filament_type", 0) == "PLA"
        assert get_filament_field(config, "filament_type", 1) == "TPU"
        assert get_filament_field(config, "filament_type", 2) == "PETG"

    def test_out_of_range_returns_none(self) -> None:
        config = {"filament_type": ["PLA", "TPU"]}
        assert get_filament_field(config, "filament_type", 5) is None

    def test_missing_field_returns_none(self) -> None:
        assert get_filament_field({}, "filament_type", 0) is None

    def test_scalar_string_semicolon(self) -> None:
        config = {"filament_colour": "#AAA;#BBB;#CCC"}
        assert get_filament_field(config, "filament_colour", 1) == "#BBB"

    def test_scalar_non_separated(self) -> None:
        # A true scalar (non-parallel) field returns the value at index 0 only.
        config = {"layer_height": "0.2"}
        assert get_filament_field(config, "layer_height", 0) == "0.2"
        assert get_filament_field(config, "layer_height", 1) is None


class TestGetUsedFilamentIndices:
    def test_reads_from_all_selectors(self) -> None:
        config = {
            "wall_filament": "1",
            "support_filament": "2",
            "support_interface_filament": "2",
            "sparse_infill_filament": "1",
            "solid_infill_filament": "1",
            "wipe_tower_filament": "0",
            "filament_colour": ["#000", "#111", "#222", "#333"],
        }
        assert get_used_filament_indices(config) == [0, 1]

    def test_zero_is_ignored(self) -> None:
        config = {
            "wall_filament": "0",
            "sparse_infill_filament": "3",
            "filament_colour": ["#A", "#B", "#C", "#D"],
        }
        assert get_used_filament_indices(config) == [2]

    def test_no_selectors_falls_back_to_all(self) -> None:
        # If no selectors present at all, treat every slot as used.
        config = {"filament_colour": ["#A", "#B"]}
        assert get_used_filament_indices(config) == [0, 1]

    def test_deduplicates_and_sorts(self) -> None:
        config = {
            "wall_filament": "3",
            "sparse_infill_filament": "1",
            "solid_infill_filament": "3",
            "filament_colour": ["#A", "#B", "#C", "#D"],
        }
        assert get_used_filament_indices(config) == [0, 2]


class TestIsFlexible:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("TPU", True),
            ("tpu", True),
            ("PEBA", True),
            ("tpe", True),
            ("PLA", False),
            ("PETG", False),
            ("", False),
            (None, False),
        ],
    )
    def test_classifies_flex(self, value: str | None, expected: bool) -> None:
        assert is_flexible(value) is expected


class TestFindRigidAlternative:
    def test_prefers_pla(self) -> None:
        config = {
            "filament_type": ["TPU", "PLA", "PETG", "TPU"],
            "filament_colour": ["#0", "#1", "#2", "#3"],
        }
        assert find_rigid_alternative(config, exclude_index=0) == 1

    def test_falls_back_to_petg_when_no_pla(self) -> None:
        config = {
            "filament_type": ["TPU", "ABS", "PETG"],
            "filament_colour": ["#0", "#1", "#2"],
        }
        assert find_rigid_alternative(config, exclude_index=0) == 2

    def test_none_when_all_flex(self) -> None:
        config = {
            "filament_type": ["TPU", "PEBA"],
            "filament_colour": ["#0", "#1"],
        }
        assert find_rigid_alternative(config, exclude_index=0) is None

    def test_excludes_the_excluded_index(self) -> None:
        config = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#0", "#1"],
        }
        assert find_rigid_alternative(config, exclude_index=0) is None


class TestParseScalarIndex:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1", 0),
            ("2", 1),
            (1, 0),
            (4, 3),
            ("0", None),
            (0, None),
            ("", None),
            (None, None),
            ("bogus", None),
        ],
    )
    def test_parses(self, value: object, expected: int | None) -> None:
        assert parse_scalar_index(value) == expected


class TestPopFilamentSlot:
    def test_pops_parallel_arrays(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C", "#D"],
            "filament_type": ["PLA", "TPU", "PETG", "ABS"],
            "filament_settings_id": ["w", "x", "y", "z"],
        }
        pop_filament_slot(config, 1, target_index=0)
        assert config["filament_colour"] == ["#A", "#C", "#D"]
        assert config["filament_type"] == ["PLA", "PETG", "ABS"]
        assert config["filament_settings_id"] == ["w", "y", "z"]

    def test_remaps_selector_pointing_at_removed(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C"],
            "wall_filament": "2",
        }
        pop_filament_slot(config, 1, target_index=0)
        assert config["wall_filament"] == "1"

    def test_decrements_higher_selector(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C"],
            "wall_filament": "3",
        }
        pop_filament_slot(config, 1, target_index=0)
        assert config["wall_filament"] == "2"

    def test_lower_selector_unchanged(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C"],
            "wall_filament": "1",
        }
        pop_filament_slot(config, 1, target_index=0)
        assert config["wall_filament"] == "1"

    def test_clears_selector_when_no_target(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C"],
            "wall_filament": "2",
        }
        pop_filament_slot(config, 1)
        assert config["wall_filament"] == "0"

    def test_skips_non_parallel_field(self) -> None:
        config = {
            "filament_colour": ["#A", "#B", "#C"],
            "filament_map": ["1", "2", "3", "4"],  # length 4, not count 3 — skipped
        }
        pop_filament_slot(config, 1, target_index=0)
        assert config["filament_map"] == ["1", "2", "3", "4"]
        assert config["filament_colour"] == ["#A", "#C"]

    def test_out_of_range_is_noop(self) -> None:
        config = {"filament_colour": ["#A", "#B"]}
        import copy

        snapshot = copy.deepcopy(config)
        pop_filament_slot(config, 5)
        assert config == snapshot
