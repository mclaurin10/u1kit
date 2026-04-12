# Decisions

Design decisions and open questions for u1kit Phase 1.

## Archive fidelity

**Decision:** Preserve original compression method, entry order, and mtimes for all
non-config entries on round-trip. Rewritten config entries use `ZIP_DEFLATED`. This
ensures mesh data, thumbnails, and relationships are byte-identical.

**Open question:** Whether Snapmaker Orca cares about ZIP compression level, entry
ordering, or timestamps has not been verified. Flagged for a real-file spike once
we have actual .3mf samples from the printer.

## Config emit format

**Decision:** JSON serialized with sorted keys, 4-space indent, trailing newline.
This matches Orca Slicer's observed output format.

## A3 G-code template

**Decision:** Toolchange G-code loaded from `u1kit/data/u1_toolchange.gcode` at
runtime so swapping templates is a single-file change.

**TODO:** Replace placeholder with known-good Snapmaker Orca export.

## U1 printer reference

**Decision:** Printer profile data loaded from `u1kit/data/u1_printer_reference.json`.

**TODO:** Replace placeholder values with real Snapmaker U1 specs.

## B1 filament count

**Decision:** Report-only in Phase 1. Raises `fail` severity with no fixer.
Interactive merge of filaments deferred to Phase 2.

## Reference JSON shape (Phase 1 contract fix)

**Decision:** Machine limit fields (`machine_max_acceleration_*`, `machine_max_speed_*`,
`machine_max_jerk_*`) stored as single-element arrays (e.g. `["5000"]`) to match Orca
Slicer's actual .3mf output format. Profile identity fields (`printer_settings_id`,
`printer_model`, `printable_area`, `printable_height`) remain scalar strings.

## B3 inherits broadening (Phase 1 contract fix)

**Decision:** B3 rule and fixer now flag/remove `inherits` when it does not match
`\bU1\b` (word-boundary, case-insensitive), rather than only when it contains "Bambu"
or "BBL". This catches non-standard profile chains (e.g. third-party slicer profiles)
that are not U1-compatible.

## B3 compatible_printers word boundary (Phase 1 contract fix)

**Decision:** `compatible_printers` filtering uses `\bU1\b` regex instead of substring
match. Prevents false positives like "U1Megatron" from being treated as U1-compatible.

## D1 malformed fixer_id (Phase 1 contract fix)

**Decision:** When `mixed_filament_height_lower_bound` is not a valid number, the D1
rule now returns `fixer_id="d1"`. The D1 fixer unconditionally overwrites all three
height fields with `uniform_height`, so it handles malformed values correctly without
reading the old value.

## Pipeline dead code (Phase 1 contract fix)

**Decision:** Removed the post-fix re-lint and unused `remaining_fails` block from
`Pipeline.run()`. Callers re-lint independently if they need post-fix validation.

## Preset path parsing (Phase 1 contract fix)

**Decision:** `_list_presets()` uses `Traversable.name` instead of `str().rsplit()`
path decomposition for cross-platform correctness.

## D1 in bambu-to-u1 preset (Phase 1 contract fix)

**Decision:** Added D1 to the bambu-to-u1 preset rules list. D1 only fires when Full
Spectrum keys (`mixed_filament_height_*`) are present, so it is a no-op for Bambu
files. Without it, the CLI `fix` command could never address height bound issues.

## Python version floor

**Decision:** `requires-python = ">=3.10"`. The original plan specified 3.11+ but
nothing in the codebase uses 3.11-only features (no `tomllib`, `typing.Self`,
`typing.LiteralString`, `ExceptionGroup`, or `TaskGroup`). Every module uses
`from __future__ import annotations` for PEP 604 union syntax. pyproject.toml,
`[tool.mypy] python_version`, and `[tool.ruff] target-version` are all set to 3.10.

## Filament config location

**Decision:** Filament configs are stored as per-object JSON entries within the .3mf
archive at paths matching `Metadata/plate_*/slice_info.config` or as embedded JSON
within `project_settings.config` under filament_settings_id / filament_colour etc.
The actual structure will be adapted once real samples are available.
For Phase 1, we treat filament data as arrays embedded in project_settings.config.
