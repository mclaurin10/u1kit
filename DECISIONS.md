# Decisions

Design decisions and open questions for u1kit. Phase 1 contract fixes and
Phase 2 ground-truth resolutions both live here. New decisions (and any
Phase 2 implementation notes that deviate from the proposed resolutions below)
should be appended in the same commit that introduces them.

## Archive fidelity

**Decision:** Preserve original compression method, entry order, and mtimes for all
non-config entries on round-trip. Rewritten config entries use `ZIP_DEFLATED`. This
ensures mesh data, thumbnails, and relationships are byte-identical.

**Resolved 2026-04-12:** Round-trip against `tests/fixtures/real/u1_native.3mf`
(a real Snapmaker Orca native export) passes byte-identical on all non-config
entries, entry count, and entry order. See
`tests/test_archive_roundtrip.py::TestRealFileRoundtrip::test_u1_native_roundtrip_preserves_bytes`.

## Config emit format

**Decision:** JSON serialized with sorted keys, 4-space indent, trailing newline.
This matches Orca Slicer's observed output format.

## A3 G-code template

**Decision:** Toolchange G-code loaded from `u1kit/data/u1_toolchange.gcode` at
runtime so swapping templates is a single-file change. The template is the raw
`change_filament_gcode` string stored in a .3mf's `project_settings.config`, using
Orca Slicer's template language (`{variable}` / `[variable]` placeholders, `if/then/
endif` blocks). u1kit writes this value into the config field verbatim; Orca
evaluates the template at slice time.

## U1 printer reference

**Decision:** Printer profile data loaded from `u1kit/data/u1_printer_reference.json`.
The reference includes 36 fields extracted from a real Snapmaker Orca slice:
identity fields (`printer_settings_id`, `printer_model`, `printer_variant`), geometry
(`printable_area` as list of corner strings, `printable_height` as scalar), per-
extruder arrays (machine limits, nozzle_diameter, extruder_offset, etc.), and toolchanger
metadata (`single_extruder_multi_material`, `nozzle_type`).

**Source:** Extracted on 2026-04-12 from `u1.3mf` (Snapmaker Orca export, template
date 20251213 per machine_start_gcode header).

## B1 filament count

**Decision:** Report-only in Phase 1. Raises `fail` severity with no fixer.
Interactive merge of filaments deferred to Phase 2.

## Reference JSON shape

**Decision:** Per-extruder fields are stored as 4-element arrays (one value per
extruder), matching Snapmaker Orca's actual output for the U1 toolchanger. This
includes `machine_max_*` (acceleration/speed/jerk/junction_deviation on every axis,
including `_e` for filament), `nozzle_diameter`, `extruder_offset`, and
`required_nozzle_HRC`. Values may differ per extruder (e.g. `machine_max_jerk_z`
is `["3", "3", "0.4", "0.4"]`).

`printable_area` is a list of 4 corner strings (e.g. `["0.5x1", "270.5x1",
"270.5x271", "0.5x271"]`). Identity fields (`printer_settings_id`, `printer_model`,
`printable_height`, `printer_variant`, etc.) are scalar strings.

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

**Verified 2026-04-12 against `tests/fixtures/real/u1_native.3mf`:** filament fields
are flat parallel arrays on `project_settings.config`. There are no per-plate
filament configs on Snapmaker Orca native exports. Every per-filament field
(`filament_type`, `filament_colour`, `filament_max_volumetric_speed`, `hot_plate_temp`,
`textured_plate_temp`, `slow_down_layer_time`, `z_hop`, etc.) is stored as a list
whose length equals the filament count. Selectors (`wall_filament`,
`support_filament`, `sparse_infill_filament`, `solid_infill_filament`,
`wipe_tower_filament`, `support_interface_filament`) are scalar 1-based indices
into those arrays. Phase 1's pragmatic choice was correct; Phase 2 centralizes
access in `u1kit/filaments.py`.

## Phase 2 open questions

Twenty ambiguities discovered while planning Phase 2, with proposed resolutions
locked here. Each subsequent task assumes these; any task hitting counter-evidence
must update this section in the same commit.

1. **B1 color-distance metric** — **CIEDE2000** (perceptually accurate,
   stdlib-implementable in <80 LoC, tested against Sharma et al. 2005 reference
   values).
2. **B1 merge direction** — when merging filament *j* into filament *i*, the
   filament whose index appears **first in the used-set** stays; the other's
   selector references are remapped to it and its parallel-array entries are
   dropped.
3. **B1 interactive UI** — **one y/n per proposed merge**, with an "all at once"
   shortcut. Richer editing is deferred to the Phase 3 GUI.
4. **B4 line cross-section formula** — `outer_wall_line_width × layer_height` for
   outer-wall cap, inner-wall cap; `sparse_infill_line_width × layer_height` for
   infill. Conservative factor = **0.8**.
5. **B5 rigid alternative criterion** — any filament whose `filament_type` is in
   `{PLA, PETG, ABS, ASA, PC}` and whose index is not the flexible one. Prefer
   PLA, fall back to the remaining preferred order, then alphabetical.
6. **C1/C2 "share a plate"** — no plate abstraction exists in U1 native. Resolved:
   *used-set* (from the selector scalars) + *parallel arrays*. ≥2 distinct values
   among used indices of a per-filament array triggers the rule.
7. **C2 safe textured-PEI first-layer cap** — **65°C**.
8. **C2 `first_layer_bed_temperature` absence** — U1 native doesn't have this
   field. C2 operates on whichever `*_plate_temp_initial_layer` arrays the config
   actually contains, falling back to `hot_plate_temp_initial_layer`. If none
   present, C2 emits no Result.
9. **D2 Z-hop primary source** — flag if `max(z_hop[i], filament_z_hop[i]) ≥
   5 × layer_height` for any used filament. Fix writes the capped value back to
   `z_hop[i]` and zeroes `filament_z_hop[i]` to avoid the override.
10. **D3 toolchange estimate formula** — `layer_count × #mixed_definitions_with_ratio_50`
    (≈ one toolchange per layer per 1:1 blend). Informational only — magnitude
    matters, not exact count.
11. **E1 thinnest-feature detection** — take the minimum of the object's
    bounding-box XY dimensions from `3D/3dmodel.model`. True mesh analysis is out
    of scope; bounding-box min is a safe lower bound for warn-level guidance.
12. **E1 `line_width` choice** — `outer_wall_line_width` (the tightest constraint
    in practice).
13. **E2 volumetric speed** — minimum across the used-set (the slowest filament
    dominates).
14. **E3 plate-size threshold** — **120 × 120 mm** (roughly half the U1 bed);
    tunable via preset option.
15. **E3 prime tower brim bump** — `max(current_prime_tower_brim_width, 5)` mm.
    Warn-level, auto-fix optional.
16. **F1 lineage heuristic** — regex `r" @[A-Za-z0-9 ]+$"` on each used filament's
    `filament_settings_id`. Missing suffix or non-`@Snapmaker U1` suffix emits an
    info-level result. Matches the U1 native pattern observed in `u1.3mf`.
17. **Interactive UX — Click vs prompt_toolkit** — **Click only**, using
    `click.confirm()` + `click.prompt()` + `difflib.unified_diff`. Prompt_toolkit
    is reserved for the Phase 3 GUI. Rationale: no new dependency, CliRunner tests
    stay simple.
18. **User preset dir on Windows** — use `platformdirs.user_config_path("u1kit")
    / "presets"`. New dependency `platformdirs >= 3`.
19. **Archive fidelity vs real file** — resolved by Task 1 (see "Archive fidelity"
    above).
20. **Fixture corpus** — Phase 2 starts with `tests/fixtures/real/u1_native.3mf`.
    Additional Bambu/Makerworld/FS samples will be added as available; Phase 2
    is not blocked on corpus completeness.

**Parse-and-preserve note (D3):** `mixed_filament_definitions` is a semicolon-CSV
whose 5th field (index 4) is the ratio percent. Exact semantics of positions 2, 3,
5–11 are deferred: Phase 2 parses only the fields we use (filament indices, ratio)
and preserves the rest as opaque strings so round-trip fidelity is maintained.

## Phase 2 wrap-up resolutions (2026-04-19)

Five resolutions locked before executing W1–W4 of the Phase 2 wrap-up. They
extend items 13–16 above with implementation-level specifics and introduce
preset-level options routing needed by E3's opt-in fixer.

21. **E2 estimated-layer-time formula (extends item 13)** —
    `layer_volume_mm3 = plate_footprint_mm² × layer_height`;
    `min_layer_time_s = layer_volume_mm3 / min(filament_max_volumetric_speed[used])`.
    (Correction: the earlier draft of this resolution had a `× vmax / 60` form
    that was dimensionally incorrect — `filament_max_volumetric_speed` is in
    mm³/s, so dividing volume by vmax yields seconds directly.) If
    `min_layer_time_s < max(slow_down_layer_time[used])` for any used filament,
    emit one `info`-severity result. Plate footprint comes from
    `u1kit.geometry.total_plate_footprint(context.geometry_bounds)`; the used-set
    comes from `u1kit.filaments.get_used_filament_indices(config)`. No fixer —
    the user must decide whether to raise volumetric speed, lower the cooling
    minimum, or accept the clamp.
22. **E3 opt-in fixer gate (extends items 14, 15)** — E3's rule fires at `warn`
    severity when plate footprint min-dimension < 120 mm AND
    `prime_tower_brim_width < 5` mm AND a prime tower is in use (`prime_tower_enable`
    truthy OR `wipe_tower_filament` set). The fixer bumps
    `prime_tower_brim_width` to `max(current, 5)` mm **only when
    `context.options["e3_auto_bump"] is True`**; otherwise it raises
    `E3BrimBumpNotRequested(FixerAbort)` and the pipeline records a skipped
    FixerResult. Rationale: bumping brim costs filament and print time; keep
    default behavior conservative.
23. **F1 lineage finding shape (extends item 16)** — For each index in
    `get_used_filament_indices(config)`, read `filament_settings_id[i]`. If the
    value is missing, empty, or its trailing ` @<suffix>` (matched by
    `r" @([A-Za-z0-9 ]+)$"`) is not exactly `Snapmaker U1`, emit one
    `info`-severity result per offending slot naming the 1-based slot index and
    the filament type. No fixer — the manual fix is rebuild-from-base or
    SD-card workflow, both out of scope for u1kit.
24. **Preset YAML schema (formalized)** — Every preset file has top-level
    `name` (string), `description` (string), and `rules` (list of uppercase rule
    IDs). An optional top-level `options` dict may declare fixer-tunable flags
    (see item 25). All four new presets (`fs-uniform`, `peba-safe`,
    `plus-peba-multi`, `makerworld-import`) follow this shape exactly.
25. **Preset options routing (new)** — `u1kit.cli._load_preset()` returns both
    `rules` and `options`; the `fix` command merges `preset_options` into the
    `Context.options` dict before constructing the pipeline. CLI flags take
    precedence over preset-declared options (CLI values overwrite preset values
    in the merged dict). This is the plumbing required to gate E3's fixer
    behind `e3_auto_bump: true` in `peba-safe` / `plus-peba-multi` presets.
    Built inline with W2 so E3's tests have something to exercise.
