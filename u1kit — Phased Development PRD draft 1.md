u1kit — Phased Development PRD draft 1
Phase 1 — Core library + CLI + Bambu→U1 happy path
Goal: a Python package that a Makerworld downloader can pip install and run on a .3mf to get a working U1 file.
Deliverables:

u1kit Python package. Modules: archive (.3mf read/write, preserves non-config entries byte-identical), config (parse/emit Metadata/project_settings.config and filament JSONs), rules (rule base class, registry), fixers (fixer base class, pipeline with dry-run/auto/interactive modes), report (JSON + human-readable text).
Rule base contract: check(context) -> Result(severity, message, fixer_id | None, diff_preview). Rules are pure; fixers mutate a working copy.
Bundled u1_printer_reference.json as source of truth for A2.
CLI: u1kit lint FILE, u1kit fix FILE [--preset X] [--dry-run] [--interactive] [--out PATH], u1kit presets list, --json on all commands.
Top-5 rules implemented: A2, A3, B2, B3, D1. (A1 is a free prerequisite since it gates everything; count it as 5+1.)
Preset: bambu-to-u1 (report-only B1 until Phase 2).
Tests: fixture-based. Real .3mf samples in tests/fixtures/ covering Bambu 4-color, Makerworld download, Full Spectrum mixed-layer, Snapmaker Orca native.

Exit criteria: a Makerworld Bambu 4-color .3mf runs through u1kit fix --preset bambu-to-u1 and opens in Snapmaker Orca without errors.
Phase 2 — Remaining rules + full preset library
Deliverables:

Rules: B1 (interactive merge-by-color-distance), B4, B5, C1, C2, C3, C4, D2, D3, E1, E2, E3, F1.
Presets shipped: peba-safe, plus-peba-multi, fs-uniform, makerworld-import. User-defined preset loading from ~/.config/u1kit/presets/.
Interactive mode UX for the CLI (prompt-toolkit or equivalent): per-finding accept/skip/edit.
Diff preview before apply.

Exit criteria: every rule in the v0 spec is implemented and covered by at least one fixture test; all 5 starter presets runnable.
Phase 3 — GUI (Tauri + React + Vite + Tailwind + shadcn/ui)
Architecture: Tauri app bundles the u1kit CLI as a sidecar binary (PyInstaller-built single-file exec per platform). Frontend invokes it via Command, parses --json output, never touches .3mf internals itself.
Deliverables:

Drop-zone for .3mf. Runs lint --json, renders findings grouped by severity using shadcn Accordion + Badge.
Per-finding: expand to show diff, checkbox to include in fix run, "Why?" link to rule doc.
Preset picker (shadcn Select), custom preset editor later.
"Apply fixes" → calls fix with selected findings → shows result, offers save-as.
Settings: default preset, default output location, path to CLI binary override.

Svelte swap: if chosen, same architecture — only the frontend changes. Tauri + sidecar boundary is framework-agnostic.
Exit criteria: non-technical user can drop a file, pick a preset, apply, and save without opening a terminal.
Phase 4 — Sanitizer, batch, polish
Deliverables:

u1kit sanitize FILAMENT.json — standalone filament-JSON cleaner sharing B3's logic. Both CLI command and GUI tab.
u1kit fix --batch DIR/ with parallelism and a summary report.
Rule authoring docs + plugin discovery (entry points) so third parties can ship rule packs.
Homebrew tap, winget manifest, AUR PKGBUILD.
Optional: watch-mode (u1kit watch ~/Downloads --preset makerworld-import) for auto-processing Makerworld downloads.


Open questions to resolve before Phase 1 kickoff

Archive fidelity — does Snapmaker Orca care about .3mf ZIP compression level / entry ordering / timestamps? If yes, round-tripping needs to preserve them. Worth a 1-hour spike before writing archive.
A3 toolchange sequence — the "U1-equivalent toolchange sequence" needs to be pinned down as a literal G-code template. Pull from a known-good Snapmaker Orca export and check it in as u1kit/templates/u1_toolchange.gcode.
B1 interactive merge — CLI-only for Phase 2, or defer the merge UI to Phase 3 where shadcn makes it pleasant? Recommend: CLI shows the proposed merge table and asks y/n; real editing waits for GUI.
Rule IDs as stable API — lock the A2/D1 IDs as the public identifier for presets and --only/--skip flags. Renaming later breaks user presets.