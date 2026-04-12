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

## Filament config location

**Decision:** Filament configs are stored as per-object JSON entries within the .3mf
archive at paths matching `Metadata/plate_*/slice_info.config` or as embedded JSON
within `project_settings.config` under filament_settings_id / filament_colour etc.
The actual structure will be adapted once real samples are available.
For Phase 1, we treat filament data as arrays embedded in project_settings.config.
