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

| ID | Severity | Description |
|----|----------|-------------|
| A1 | info | Detect source slicer (gates downstream rules) |
| A2 | fail | Printer profile must be U1 |
| A3 | fail | Strip Bambu AMS macros, insert U1 toolchange |
| B1 | fail | Filament count must be ≤ 4 (report-only) |
| B2 | fail | Every filament needs extruder index 1–4 |
| B3 | warn | Remove Bambu-specific filament fields |
| D1 | fail | Mixed height bounds must be ≥ layer height |

## Exit criteria

A Makerworld Bambu 4-color .3mf, run through `u1kit fix --preset bambu-to-u1`,
opens in Snapmaker Orca without errors. All Phase 1 rules have passing fixture
tests. `u1kit lint --json` and `u1kit fix --json` produce stable, documented schemas.

## Status

Phase 1 is complete. Covered: rules A1, A2, A3, B1, B2, B3, D1 with fixers for
A2, A3, B2, B3, D1; `u1kit lint`, `u1kit fix`, `u1kit presets list` with the
`bambu-to-u1` preset; archive round-trip that preserves thumbnails and mesh
data byte-for-byte; stable JSON schema (`schema_version: "1"`); real Snapmaker
U1 printer reference and toolchange G-code sourced from an Orca export.

Deferred to Phase 2: rules B4, B5, C1–C4, D2, D3, E1–E3, F1 and the interactive
filament-merge workflow for >4 filament inputs (B1 is report-only today).

## Development

```bash
pip install -e ".[dev]"
pytest
mypy --strict u1kit/
ruff check u1kit/ tests/
```
