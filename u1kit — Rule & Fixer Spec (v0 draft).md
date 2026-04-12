u1kit — Rule & Fixer Spec (v0 draft)
Rules grouped by category. Each entry: what it checks → severity → auto-fix behavior. Severities: fail (file will not print correctly), warn (risky, context-dependent), info (cosmetic/optimization).
A. Printer profile & origin
A1. Source slicer identification → info → Detect Bambu Studio / vanilla Orca / Snapmaker Orca / Full Spectrum Orca / Prusa by inspecting Metadata/project_settings.config printer name, printer_model, and presence of Full Spectrum–specific keys (mixed_filament_height_*). No fix; gates downstream rules.
A2. Printer profile not U1 → fail → Rewrite printer_settings_id, printer_model, bed shape, and machine_max_* kinematics to U1 values. Source of truth: a bundled u1_printer_reference.json.
A3. Bambu AMS G-code macros present → fail → Scan machine_start_gcode, machine_end_gcode, change_filament_gcode, layer_change_gcode for M620/M621/M623/AMS syntax; strip and replace with U1-equivalent toolchange sequence.
B. Filament & toolhead
B1. Filament count > 4 → fail → Report; refuse auto-fix (requires user intent to consolidate). Offer interactive mode to merge by color distance.
B2. Filament-to-tool mapping missing or invalid → fail → Ensure each used filament has a filament_map/extruder index in 1–4. Auto-assign by first-use order if missing.
B3. BBL-specific filament fields → warn → Remove filament_extruder_variant, inherits chains referencing Bambu profiles, and compatible_printers entries pointing to non-U1 printers. (Shared logic with the profile-sanitizer tool.)
B4. Per-filament speed overrides missing for flexibles → warn → If any filament's filament_type is TPU/PEBA and it lacks explicit per-filament speed caps, inject conservative overrides (outer wall, inner wall, infill) derived from filament_max_volumetric_speed × line cross-section. Belt-and-suspenders against under-extrusion.
B5. Flexible filament used as its own support → warn → If support filament = support interface filament = a flexible, recommend rigid alternative (PLA). Auto-fix: if a rigid PLA is present in the filament list, reassign support to it; else warn only.
C. Multi-material plate conflicts
C1. Bed temperature conflict → fail → When ≥2 filaments with different hot_plate_temp/textured_plate_temp share a plate, pick the lower-common value and apply to curr_bed_type temp field. Surface the conflict in the report.
C2. First-layer bed temp conflict → fail → Same logic for first_layer_bed_temperature. Additional rule: if PEI textured and any filament >65°C first-layer, cap at safe textured-PEI range.
C3. Minimum cooling time mismatch → warn → Use the maximum slow_down_layer_time across filaments on the plate (most conservative wins). PEBA's 12s trumps PLA's 4s.
C4. Fan speed range conflict → info → No single fix; surface per-filament ranges and note that per-filament fan settings will apply automatically at toolchange.
D. Full Spectrum / mixed-layer specific
D1. Mixed-filament height bounds below layer_height → fail → Detect when mixed_filament_height_lower_bound < layer_height. Auto-fix: lock all three (layer_height, mixed_filament_height_lower_bound, mixed_filament_height_upper_bound) to the same uniform value (default 0.2mm, configurable). This is the single biggest repeated failure mode in your history.
D2. Z-hop magnitude vs layer height → warn → Flag when Z-hop in change_filament_gcode is ≥ 5× layer_height. At 0.04mm that's the ~37-layer catastrophe; at 0.2mm it's benign. Auto-fix: cap Z-hop at max(1.5mm, 4 × layer_height).
D3. 1:1 alternation cost awareness → info → When mixed blends are defined with 1:1 ratios, surface estimated toolchange count. No fix; purely informational (this directly addresses the misconception I had in chat 0bdc).
E. Geometry & scale sanity
E1. Strut/wall line count at current scale → warn → Parse object dimensions, estimate thinnest feature; if thinnest feature ÷ line_width < 3, warn about gap-fill territory. Suggest dropping line_width or accepting perimeter-only walls.
E2. Estimated layer time clamp → info → If plate area / volumetric speed puts most layers under slow_down_layer_time, warn that slow_down_min_speed will dominate actual print speed. Relevant for small-scale prints with aggressive cooling minimums.
E3. Prime tower stability at small plate scales → warn → If plate footprint scaled below some threshold and prime tower brim width is default, suggest bumping prime_tower_brim_width for stability. Prime tower tip-over is a real failure.
F. Build & sending
F1. Print Preprocessing dialog compatibility → info → Detect filament profiles that are likely to trigger Snapmaker Orca's Print Preprocessing rejection (custom profiles without proper filament_settings_id lineage). Suggest SD-card workflow as workaround, or recommend rebuilding the profile from a Generic TPU base inside Snapmaker Orca. No file-level fix possible.
Presets (compositions of rules+fixers)

peba-safe → D1, D2, B4, B5, C3 — the full PEBA reliability bundle
plus-peba-multi → peba-safe + C1, C2, C4 — adds plate conflict resolution for mixed PLA/PEBA workloads
fs-uniform → D1 alone, locking mixed bounds to layer_height — the single most common fix from your Full Spectrum work
bambu-to-u1 → A2, A3, B1 (report-only), B2, B3 — classic conversion baseline
makerworld-import → bambu-to-u1 + C1, C2, B4 — typical Makerworld 4-color download case

Each preset is a YAML/JSON file the CLI and GUI both load. Users can compose their own.