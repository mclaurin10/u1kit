# u1kit

Convert Bambu/Makerworld .3mf files for the Snapmaker U1 (4-tool IDEX/toolchanger).

## Install

```bash
pip install -e .
```

## Usage

```bash
# Lint a file — report issues without fixing
u1kit lint model.3mf
u1kit lint model.3mf --json

# Fix a file — apply preset transformations
u1kit fix model.3mf --out fixed.3mf
u1kit fix model.3mf --preset bambu-to-u1 --dry-run
u1kit fix model.3mf --interactive

# List available presets
u1kit presets list
```

## Rules

| ID | Severity | Phase | Fixer | Description |
|----|----------|-------|-------|-------------|
| A1 | info | 1 | — | Detect source slicer (gates downstream rules) |
| A2 | fail | 1 | ✓ | Printer profile must be U1 |
| A3 | fail | 1 | ✓ | Strip Bambu AMS macros, insert U1 toolchange |
| B1 | fail | 1/2 | ✓ | Filament count must be ≤ 4 (interactive merge by CIEDE2000 color distance) |
| B2 | fail | 1 | ✓ | Every filament needs extruder index 1–4 |
| B3 | warn | 1 | ✓ | Remove Bambu-specific filament fields |
| B4 | warn | 2 | ✓ | Inject conservative speed caps for TPU/PEBA filaments |
| B5 | warn | 2 | ✓ | Swap flexible-as-support for a rigid alternative when available |
| C1 | fail | 2 | ✓ | Reconcile conflicting `hot_plate_temp` / `textured_plate_temp` across used filaments |
| C2 | fail | 2 | ✓ | Reconcile conflicting first-layer bed temps; cap textured-PEI at 65 °C |
| C3 | warn | 2 | ✓ | Use the max `slow_down_layer_time` across used filaments |
| C4 | info | 2 | — | Surface per-filament fan-speed ranges (applied at toolchange) |
| D1 | fail | 1 | ✓ | Mixed-filament height bounds must be ≥ layer height |
| D2 | warn | 2 | ✓ | Cap Z-hop at `max(1.5 mm, 4 × layer_height)` when ≥ 5× layer height |
| D3 | info | 2 | — | Surface estimated toolchange count from 1:1 mixed blends |
| E1 | warn | 2 | — | Warn when thinnest object feature ÷ outer-wall line width < 3 |
| E2 | info | 2 | — | Warn when cooling minimums will dominate actual print speed *(not yet shipped)* |
| E3 | warn | 2 | ✓ | Bump prime-tower brim width on small plates *(not yet shipped)* |
| F1 | info | 2 | — | Flag filament profiles without `@Snapmaker U1` lineage *(not yet shipped)* |

## Exit criteria

A Makerworld Bambu 4-color .3mf, run through `u1kit fix --preset bambu-to-u1`,
opens in Snapmaker Orca without errors. Every rule has at least one fixture
test; every fixer has a unit test and an idempotency test. `u1kit lint --json`
and `u1kit fix --json` produce stable, documented schemas (`schema_version: "1"`).

## Status

**Phase 1:** complete. Rules A1, A2, A3, B1 (report-only), B2, B3, D1 with
fixers for A2, A3, B2, B3, D1; `u1kit lint`, `u1kit fix`, `u1kit presets list`
with the `bambu-to-u1` preset; archive round-trip that preserves thumbnails
and mesh data byte-for-byte; stable JSON schema (`schema_version: "1"`); real
Snapmaker U1 printer reference and toolchange G-code sourced from an Orca
export.

**Phase 2:** 13 of 16 tasks complete. Shipped since Phase 1: real-file archive
round-trip verification, `u1kit/filaments.py` parallel-array accessor,
`u1kit/color.py` CIEDE2000 distance, `u1kit/geometry.py` 3D model parser, the
Click-based interactive UX with unified-diff preview, user preset loading from
`platformdirs.user_config_path("u1kit") / "presets"`, and rules B1 (interactive
merge), B4, B5, C1, C2, C3, C4, D2, D3, E1 with their fixers where applicable.

**Still open for Phase 2:** rules E2, E3, F1 and the preset-shipping wrap-up
(`fs-uniform`, `peba-safe`, `plus-peba-multi`, `makerworld-import` plus Phase 2
exit verification).

## Development

```bash
pip install -e ".[dev]"
pytest
mypy --strict u1kit/
ruff check u1kit/ tests/
```

All three gates must pass on every commit. `.gitattributes` normalizes line
endings to LF across platforms; if your editor saves with CRLF, the renormalize
rule will correct on checkout. Project conventions — rule/fixer contract,
commit policy, module layout — are documented in `CLAUDE.md`.
