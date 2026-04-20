# u1kit Phase 2 Wrap-Up + Phase 3 GUI — Implementation Plan

> **For Claude Code plan mode:** Execute task-by-task. Every commit passes the three gates (`pytest`, `mypy --strict`, `ruff check`) plus — for Phase 3 — `pnpm typecheck`, `pnpm lint`, `pnpm test`, and the Tauri build for the current host. No squash commits during a phase; the task-level history is the rollback unit.

**Goal:** Close the Phase 2 exit contract by shipping the last three rules (E2, E3, F1) and the four remaining starter presets with end-to-end verification. Then ship Phase 3: a Tauri + React + Vite + Tailwind + shadcn/ui desktop GUI that wraps the existing `u1kit` CLI as a PyInstaller sidecar. A non-technical user should be able to drop a `.3mf`, pick a preset, review findings, apply fixes, and save the output without opening a terminal.

**Architecture:**

- Phase 2 wrap-up continues the Phase 1/2 patterns: class-based `Rule`/`Fixer` subclasses registered in `u1kit/rules/__init__.py` and `u1kit/fixers/__init__.py`, short-form fixer IDs (`rule_id.lower()`), `from __future__ import annotations` everywhere.
- Phase 3 treats the CLI as an **opaque sidecar**. The frontend invokes `u1kit lint --json`, `u1kit fix --json`, and `u1kit presets list --json` through Tauri's `Command` API, parses the stable `schema_version: "1"` output, and **never touches `.3mf` internals itself**. No rule engine, no ZIP parsing, no YAML parsing in the GUI process.
- Rule documentation ships as static markdown bundled into the app at build time (sourced from `u1kit — Rule & Fixer Spec (v0 draft).md`). No network fetch in MVP.

**Tech stack — Phase 2:** Python 3.10+, Click, PyYAML, stdlib-only for diff / XML / color math. mypy `--strict`, ruff clean.

**Tech stack — Phase 3:** Tauri 2 (Rust 1.75+), React 18 + TypeScript strict, Vite 5, Tailwind CSS 3, shadcn/ui, pnpm as the package manager, Vitest + React Testing Library for unit tests, Playwright for E2E. PyInstaller for the sidecar bundle (one binary per `{os, arch}` target). No Svelte — PRD's Svelte swap is locked closed for this phase.

---

## Context

Phase 1 shipped the rule engine, CLI, archive round-trip, and the `bambu-to-u1` preset. Phase 2 Tasks 0–13 added `u1kit/filaments.py`, `u1kit/color.py`, `u1kit/geometry.py`, the Click-based interactive UX, user preset loading via `platformdirs`, and rules B1 (interactive merge), B4, B5, C1, C2, C3, C4, D2, D3, E1 with their fixers. Still open: E2, E3, F1 and preset shipping (Tasks 14–16 in `phase-two.md`). With those closed, every rule in the v0 spec has a fixture test and all five starter presets run end-to-end — the precondition Phase 3's PRD assumes.

Phase 3 is the first work that isn't Python. The CLI becomes an API. Every JSON field emitted by `u1kit/report.py` is now a public contract. The work falls into three bands: (1) make the CLI robust as an invoked subprocess (deterministic exits, no stdout leakage, `--json`-first), (2) stand up the Tauri/React shell and wire it to the sidecar, (3) build the UX (drop-zone → findings → fix → save) around a stable state model.

**Open DECISIONS.md items this plan must resolve:**

1. **PyInstaller vs. embedded Python interpreter for the sidecar** — PRD says PyInstaller; lock it (G0). Rationale: PRD-authoritative and single-file is simpler for cross-platform distribution than bundling CPython.
2. **Tauri 1 vs Tauri 2** — Tauri 2 is GA as of October 2024 and is the default today; lock it (G0). Rationale: mobile-ready plugins, stable config format, Windows/macOS/Linux parity.
3. **Diff rendering: client-side vs server-side** — the CLI already emits `diff_preview` strings via `difflib.unified_diff`. Client renders those as preformatted blocks in MVP. No client-side diff library in MVP.
4. **Rule doc source** — bundle `u1kit — Rule & Fixer Spec (v0 draft).md` split into per-rule markdown files at build time. No fetch. Updatable via app update.
5. **State management** — React `useReducer` for the top-level app state (`session: Idle | Linting | Findings | Fixing | Done | Error`), plus `useState` locally. No Redux/Zustand in MVP. Upgrade later if needed.
6. **Sidecar versioning** — require `u1kit --version` to return a semver string matching `package.json`'s `version` field at Tauri build time. Build fails if they diverge.
7. **Testing boundary** — unit tests in Vitest for reducers and pure components; Playwright for the one end-to-end flow (drop → lint → fix → save). No component-level snapshot tests.
8. **Signing, notarization, auto-update** — **deferred to Phase 4.** MVP ships unsigned Windows `.msi`, unsigned macOS `.dmg` with an unnotarized install instruction, and a Linux AppImage. This is called out in the README.
9. **Minimum OS versions** — Windows 10 1809+, macOS 12+, Linux glibc 2.31+ (Tauri 2 defaults).
10. **Preset source for the GUI picker** — call `u1kit presets list --json` at GUI startup; merge builtin + user presets into one list, tagged by source.

These resolutions are proposals. Task G0 locks them into `DECISIONS.md` before any UI code is written. Tasks may revise individual entries if implementation surfaces counterevidence, but must update `DECISIONS.md` in the same commit.

---

## Ground truth for Phase 3

Facts the plan must respect. These are not negotiable without bumping the CLI JSON schema version.

| Surface | Current shape | Used by |
|---|---|---|
| `u1kit lint FILE --json` | `{"schema_version": "1", "file": str, "findings": [{"rule_id": "A2", "severity": "fail", "message": str, "fixer_id": "a2" \| null, "diff_preview": str \| null}, ...]}` | G5, G6 |
| `u1kit fix FILE --json --preset P` | `{"schema_version": "1", "file": str, "preset": str, "applied": [{"fixer_id": str, "message": str}], "skipped": [{"fixer_id": str, "reason": str}], "output_path": str}` | G7 |
| `u1kit presets list --json` | `{"schema_version": "1", "presets": [{"name": str, "source": "builtin" \| "user", "rules": [str]}]}` | G7 |
| `u1kit --version` | single-line semver (e.g. `0.1.0`) | G1 |
| Exit codes | `0` clean; `1` findings with `fail` severity (on lint); `2` internal error | G5, G9 |
| Stdout policy | `--json` prints **one** JSON object to stdout, nothing else; human-readable logs go to stderr | G5, G7 |
| Rule IDs | stable API — never rename | G6 (rule doc links) |

**Implications:**

- **G5 must assume `--json` stdout is parseable without line-stripping.** If any rule accidentally writes to stdout, that's a Phase 2 regression, not a Phase 3 UI workaround. Task G1 has a test for this.
- **Exit code 1 on failing lint is expected, not an error.** G9's error handler distinguishes "CLI ran successfully and reported failures" (exit 1) from "CLI crashed" (exit 2 or non-exit).
- **G6 must degrade gracefully when `diff_preview` is `null`** — not every fixer emits a diff (e.g. informational rules).

---

## Spec ambiguities to lock in DECISIONS.md

Locked in W0 (before wrap-up work) and G0 (before GUI work). Each subsequent task assumes these.

**Phase 2 wrap-up:**

W-i. **E2 layer-area heuristic** — compute `min_layer_time` from `plate_footprint_mm2 × layer_height × filament_max_volumetric_speed_min / 60`. If `min_layer_time < max(slow_down_layer_time)` for any used filament, emit `info`. Plate footprint is the XY bounding-box area across all objects (reuse `u1kit/geometry.py`).

W-ii. **E3 plate-footprint threshold** — 120 × 120 mm (bounding-box), per DECISIONS.md item 14. Fixer bumps `prime_tower_brim_width` to `max(current, 5)` mm. Warn-level; auto-fix is opt-in via preset option `e3_auto_bump: true`.

W-iii. **F1 no-op on empty `filament_settings_id`** — if the field is missing or empty-string, emit one `info` finding per affected filament slot advising a profile rebuild. No fixer.

W-iv. **Preset YAML schema** — already established by `bambu_to_u1.yaml`; the four new presets mirror it exactly.

**Phase 3 GUI:**

G-i. **Sidecar path resolution at runtime** — use Tauri's `resolve_resource` to locate `resources/u1kit{platform_suffix}`. Dev mode falls back to `cargo run --bin u1kit-sidecar`-equivalent.

G-ii. **Drop-zone accept filter** — `.3mf` and `.zip` (some Bambu exports default to `.zip` before rename). Reject anything else with a toast.

G-iii. **Finding grouping** — by severity descending (`fail` → `warn` → `info`), Accordion default-open on the first non-empty group.

G-iv. **"Why?" link target** — opens a shadcn `Sheet` with the bundled markdown rendered by `react-markdown`. No external navigation.

G-v. **Fix selection default** — every finding with a non-null `fixer_id` is checked by default; informational-only findings (no fixer) are not checkable.

G-vi. **Save-as default filename** — `{input_stem}_u1.3mf`. Default dir is the input's parent.

G-vii. **Progress indicator** — spinner for any sidecar call that takes > 200 ms. No granular progress in MVP (CLI doesn't emit intermediate events).

G-viii. **Keyboard** — `Esc` clears selection; `Enter` triggers "Apply fixes" when a preset is selected and at least one finding is checked; full tab-order through findings.

---

## Commit policy

- One commit per task. Subject line: `feat(<area>): …` for new code, `test: …` for test-only, `docs: …` for docs-only, `chore: …` for housekeeping. Phase 3 uses prefixes `feat(gui): …`, `feat(sidecar): …`, `test(gui): …`, `chore(gui): …`.
- Every commit passes all gates for the code paths it touches. A backend-only commit doesn't need to run `pnpm test`; a frontend-only commit doesn't need to run `pytest`. A commit touching both runs both.
- No squashing during the phase.
- Tasks that span multiple commits (e.g. G10 packaging per-OS) split cleanly; each sub-commit is independently green.

---

## Progress

Phase 2 wrap-up and Phase 3 are both complete as of 2026-04-19. Every task
below landed in a single commit with the three gates green; see
`git log --oneline` for the full mapping.

| Task | Scope | Status | Commit |
|---|---|---|---|
| W0. Lock Phase 2 wrap-up resolutions in DECISIONS.md | docs | ✅ done | `6af0482` |
| W1. E2 — estimated layer time clamp | rule | ✅ done | `3a7ea80` |
| W2. E3 — prime-tower brim bump | rule + fixer | ✅ done | `8e05f33` |
| W3. F1 — Print Preprocessing lineage | rule | ✅ done | `903eb65` |
| W4. Ship remaining presets + Phase 2 exit verification | presets + e2e | ✅ done | `d1384f2` |
| G0. Lock Phase 3 resolutions in DECISIONS.md | docs | ✅ done | `5df4343` |
| G1. CLI sidecar readiness | CLI | ✅ done | `1da7b08` |
| G2. Tauri project scaffold | gui | ✅ done | `a048cdf` |
| G3. Shared TypeScript types for CLI JSON contracts | gui | ✅ done | `59be6a9` |
| G4. File drop-zone + file picker | gui | ✅ done | `259ed99` |
| G5. Lint view: findings grouped by severity | gui | ✅ done | `cc14937` |
| G6. Per-finding detail + rule doc sheet | gui | ✅ done | `40bc23f` |
| G7. Preset picker + apply-fix workflow | gui | ✅ done | `8582ac2` |
| G8. Save-as flow | gui | ✅ done | `09fafbf` |
| G9. Error and edge handling | gui | ✅ done | `46e6f4e` |
| G10. Packaging per OS + CI matrix | release | ✅ done | `3968d22` |
| G11. End-to-end UX verification + Phase 3 exit | e2e | ✅ done | `c36e359` |

**Deviations from the plan** (captured in DECISIONS.md items 39–41):
`lint` / `fix --json` kept the existing `results` / `fixers` / `summary`
shape rather than the plan's aspirational reshape (only `presets list
--json` gained the `{schema_version, presets}` wrapper in G1). Playwright
E2E was replaced by a Vitest integration test mocking the Tauri shell /
dialog / invoke APIs — Tauri+Playwright on Windows is a known tarpit and
the plan itself scoped Playwright to Linux CI only. shadcn primitives
were added on-demand per task (Button+cn in G2, Accordion+Badge in G5,
Sheet+Checkbox in G6, Select in G7, an in-house Toast in G9) instead of
bulk-scaffolded in G2.

---

# Phase 2 Wrap-Up Tasks

## Task W0: Lock Phase 2 wrap-up resolutions in DECISIONS.md

**Why:** E2, E3, and F1 each have open design questions (layer-area heuristic, brim-bump threshold, lineage regex). Locking resolutions before writing code prevents counterfactual rework.

**Files:**
- Modify: `DECISIONS.md` — append four resolutions (W-i through W-iv above). Reference the existing numbered list (items 1–20) and continue from item 21.

**Steps:**
1. Append a new section `## Phase 2 wrap-up resolutions (2026-04-XX)` to `DECISIONS.md` with four numbered entries.
2. Each entry cites the rule/fixer and the test that will assert it.
3. Commit: `docs: lock E2/E3/F1 resolutions in DECISIONS.md`

**No test.** Docs-only task.

---

## Task W1: E2 — Estimated layer time clamp (info-only rule)

**Why:** PEBA/TPU with aggressive cooling minimums (high `slow_down_layer_time`) on small-plate prints gets clamped to `slow_down_min_speed`, so "fast" slicer settings silently don't apply. Surfacing this early prevents user confusion. Info-level; no fixer.

**Files:**
- Create: `u1kit/rules/e2_layer_time_clamp.py` — `E2LayerTimeClamp(Rule)`, `severity = Severity.INFO`.
- Modify: `u1kit/rules/__init__.py` — register `E2LayerTimeClamp`.
- Create: `tests/fixtures/synth/e2_small_plate_fast_filament.json` — synthesized config with known plate area + high volumetric speed + high `slow_down_layer_time`.
- Modify: `tests/test_rules.py` — add `TestE2` class with positive case (triggers), negative case (large plate), missing geometry (no-op), and no `slow_down_layer_time` (no-op).
- Modify: `README.md` — flip E2's "not yet shipped" row.

**Steps:**
1. Implement `E2LayerTimeClamp.check`. Use `context.geometry_bounds` for plate footprint (XY bbox, mm²). Read `filament_max_volumetric_speed` and `slow_down_layer_time` from `context.config` as parallel arrays; derive the used-set via `u1kit/filaments.py`.
2. Compute `min_layer_time = plate_footprint_mm2 × layer_height × min(filament_max_volumetric_speed[used]) / 60`. Compare to `max(slow_down_layer_time[used])`. Emit one `Result` if smaller.
3. Message: `"Estimated layer time ({min_layer_time:.1f}s) is below the cooling minimum ({max_slow_down}s); slow_down_min_speed will dominate actual print speed."`
4. `fixer_id = None`.
5. Write 4 tests as listed in Files. No idempotency test (no fixer).
6. Gates (pytest, mypy, ruff). Commit: `feat(e2): estimated layer-time clamp info rule`

**Test:** 4 unit tests in `tests/test_rules.py::TestE2`.

---

## Task W2: E3 — Prime-tower brim bump (warn + opt-in fixer)

**Why:** On small scaled plates with default prime-tower brim width, the tower tips over. The spec says "warn" with an auto-fix that's opt-in via preset option (DECISIONS.md item 15). Shipping the fixer behind a preset flag (`e3_auto_bump: true`) keeps the default behavior conservative.

**Files:**
- Create: `u1kit/rules/e3_prime_tower_brim.py` — `E3PrimeTowerBrim(Rule)`, `severity = Severity.WARN`.
- Create: `u1kit/fixers/e3_prime_tower_brim.py` — `E3PrimeTowerBrim(Fixer)`. Only runs when `context.options.get("e3_auto_bump") is True`; otherwise raises `E3BrimBumpNotRequested(FixerAbort)`.
- Modify: `u1kit/rules/__init__.py`, `u1kit/fixers/__init__.py` — register.
- Modify: `tests/test_rules.py` — add `TestE3`. Positive, negative (large plate), boundary (exactly 120 mm).
- Modify: `tests/test_fixers.py` — add `TestE3Fixer` with `test_apply_when_enabled`, `test_aborts_when_not_requested`, `test_idempotent`.
- Modify: `README.md` — flip E3's "not yet shipped" row.

**Steps:**
1. Rule: `plate_footprint_bounding_box_min(ObjectBounds) < 120 mm` AND `prime_tower_brim_width < 5 mm` AND a prime tower is in use (`prime_tower_enable` truthy OR `wipe_tower_filament` is set).
2. Fixer: set `prime_tower_brim_width = max(current, 5)`. Idempotent.
3. Fixer refuses without `e3_auto_bump=true`; pipeline records a `FixerResult(applied=False, reason="requires opt-in via preset option 'e3_auto_bump'")`.
4. Tests (6 total: 3 rule + 3 fixer including idempotency).
5. Gates. Commit: `feat(e3): prime-tower brim bump with opt-in fixer`

**Test:** 6 unit tests across `test_rules.py` and `test_fixers.py`.

---

## Task W3: F1 — Print Preprocessing dialog compatibility (info, no fixer)

**Why:** Snapmaker Orca's "Print Preprocessing" dialog rejects filament profiles without proper `@Snapmaker U1` lineage. Surfacing this pre-send saves a round trip. Info-only — the fix is manual (rebuild profile from Generic TPU base, or use SD-card workflow).

**Files:**
- Create: `u1kit/rules/f1_preprocessing_lineage.py` — `F1PreprocessingLineage(Rule)`, `severity = Severity.INFO`.
- Modify: `u1kit/rules/__init__.py` — register.
- Modify: `tests/test_rules.py` — add `TestF1`: positive (missing `@`), positive (foreign `@`), negative (`@Snapmaker U1`), empty-string (emit advise).
- Modify: `README.md` — flip F1's "not yet shipped" row.

**Steps:**
1. Read `filament_settings_id` (parallel array). For each used filament, apply regex `r" @[A-Za-z0-9 ]+$"` (DECISIONS.md item 16). If no match or suffix ≠ `@Snapmaker U1`, emit one finding per offending slot.
2. Message: `"Filament slot {i+1} ({filament_type[i]}) lacks @Snapmaker U1 lineage ({settings_id!r}). This may trigger Snapmaker Orca's Print Preprocessing rejection — consider rebuilding from a Generic {filament_type[i]} base or using the SD-card workflow."`
3. `fixer_id = None`.
4. Tests (4).
5. Gates. Commit: `feat(f1): Print Preprocessing lineage info rule`

**Test:** 4 unit tests.

---

## Task W4: Ship remaining presets + Phase 2 exit verification

**Why:** Phase 2's exit contract requires all 5 starter presets runnable and every rule to have a fixture test. This task ships the four outstanding preset files, adds one end-to-end test per preset, and runs the full exit checklist.

**Files:**
- Create: `u1kit/presets/fs_uniform.yaml` (rules: `[D1]`)
- Create: `u1kit/presets/peba_safe.yaml` (rules: `[D1, D2, B4, B5, C3]`)
- Create: `u1kit/presets/plus_peba_multi.yaml` (rules: `[D1, D2, B4, B5, C3, C1, C2, C4]`)
- Create: `u1kit/presets/makerworld_import.yaml` (rules: `[A2, A3, B1, B2, B3, D1, C1, C2, B4]`)
- Modify: `tests/test_cli.py::TestPresets` — add `test_all_starter_presets_list` asserting all 5 names appear.
- Create: `tests/test_phase2_e2e.py` — one test per preset. Each test synthesizes or loads a fixture exercising the preset's rules, runs `fix`, and asserts the output re-lints clean (no findings at the severities the preset is meant to address).
- Modify: `README.md` — move from "Phase 2: 13 of 16 tasks complete" to "Phase 2: complete". Update status section. Tag E2/E3/F1 as shipped in the rule table (remove the "not yet shipped" suffix).
- Modify: `phase-two.md` — mark T14–T16 done in the Progress table.
- Modify: `DECISIONS.md` — append any wrap-up implementation notes (e.g., if E3's `prime_tower_enable` heuristic was tweaked).

**Steps:**
1. Create the four YAML files. Mirror the `bambu_to_u1.yaml` shape exactly. Lowercase rule IDs in `rules:`.
2. Add `test_all_starter_presets_list` to confirm preset discovery.
3. Write `test_phase2_e2e.py`. Each test: a minimal fixture, `cli fix --preset X --out /tmp/…`, `cli lint /tmp/…`, assert the targeted severities are gone.
4. Run the full Phase 2 exit checklist (from `phase-two.md`): every rule has ≥1 test, every fixer has unit + idempotency tests, all three gates green, `u1.3mf` still round-trips byte-identical, all 5 presets resolve, `lint --json` on the fixture is schema_version "1" with no regressions.
5. Update READMEs.
6. Commit: `feat(phase2): ship remaining presets and verify exit criteria`

**Test:** +1 CLI test + 4 e2e tests = 5 new tests. Must also confirm no existing tests regress.

---

# Phase 3 GUI Tasks

## Task G0: Lock Phase 3 resolutions + verify Phase 2 exit

**Why:** Before any UI code, the 10 decisions enumerated above (PyInstaller, Tauri 2, diff-as-text, bundled docs, useReducer, sidecar versioning, test boundary, signing deferral, min OS, preset merge) are recorded in `DECISIONS.md`. Also re-runs Phase 2 exit checks as a gate.

**Files:**
- Modify: `DECISIONS.md` — append `## Phase 3 open questions (locked 2026-XX-XX)` with 10 entries.
- No code changes.

**Steps:**
1. Verify Phase 2 exit: `pytest`, `mypy --strict`, `ruff check`, `u1kit lint tests/fixtures/real/u1_native.3mf --json` emits schema_version "1" with 0 fail-severity findings, `u1kit presets list` shows all 5 starters.
2. Append the 10 resolutions to `DECISIONS.md`.
3. Commit: `docs: lock Phase 3 open questions`

**No test.**

---

## Task G1: CLI sidecar readiness

**Why:** The CLI is about to be invoked as a subprocess by a Rust frontend. Any stdout leakage, non-deterministic exit codes, or missing `--version` will surface as mysterious GUI bugs later. Harden now.

**Files:**
- Modify: `u1kit/cli.py` — add `@click.version_option(package_name="u1kit")` to `main`. Ensure every `click.echo` that isn't the `--json` payload goes to `err=True`. Ensure exit codes: `0` clean, `1` findings with fail severity on `lint`, `2` internal error (via `click.ClickException` subclass).
- Modify: `u1kit/report.py` — add module-level constant `SCHEMA_VERSION = "1"`. Export on all JSON responses.
- Create: `tests/test_cli_sidecar.py` — new test module:
  - `test_version_matches_package_version` — runs `u1kit --version`, asserts it matches `importlib.metadata.version("u1kit")`.
  - `test_lint_json_stdout_is_pure` — runs `cli(…, '--json')` with `CliRunner`, splits stdout by lines, asserts every line is parseable by `json.loads` *or* the entire stdout is one JSON object. Asserts stderr has the logs.
  - `test_lint_exit_code_1_on_fail` — fixture with a fail-severity finding, assert exit code is 1.
  - `test_fix_json_contract` — assert shape of `fix --json` output matches documented schema.
  - `test_presets_list_json_contract` — same for presets list.
- Create: `scripts/build_sidecar.py` — PyInstaller driver. One-file mode, target-triple-aware output name (`u1kit-x86_64-pc-windows-msvc.exe`, etc.). Emits to `dist/sidecar/`.
- Create: `pyinstaller.spec` if the driver needs custom data includes (`u1kit/data/*.json`, `u1kit/data/*.gcode`, `u1kit/presets/*.yaml`).

**Steps:**
1. Audit `u1kit/cli.py` for stray `click.echo(..., err=False)` in non-`--json` paths.
2. Audit for `print` calls — there should be none; all stdout routing through `click.echo`.
3. Add the 5 sidecar tests.
4. Write `scripts/build_sidecar.py`. Verify on host OS that it produces a working binary that passes `u1kit --version`, `u1kit lint fixture.3mf --json`, and `u1kit fix fixture.3mf --json`.
5. Add PyInstaller to dev extras: `pyinstaller>=6.5` (comment that it is only needed for release builds).
6. Add `dist/` to `.gitignore` if not present.
7. Gates. Commit: `feat(cli): sidecar readiness - stable stdout/exit codes and PyInstaller builder`

**Test:** 5 new tests in `test_cli_sidecar.py`. All three gates green. Manual check: run `python scripts/build_sidecar.py`, execute the binary.

---

## Task G2: Tauri project scaffold

**Why:** Stand up the Tauri 2 shell, Vite+React+TS, Tailwind, and shadcn/ui with a minimal "hello u1kit" window. Every subsequent GUI task builds on this.

**Files:**
- Create: `gui/` — Tauri project root.
  - `gui/package.json` — pnpm workspace leaf, scripts: `dev`, `build`, `tauri dev`, `tauri build`, `typecheck`, `lint`, `test`.
  - `gui/pnpm-lock.yaml`, `gui/.npmrc` (enable strict-peer-dependencies).
  - `gui/vite.config.ts`, `gui/tsconfig.json` (strict: true, noUncheckedIndexedAccess, exactOptionalPropertyTypes), `gui/tailwind.config.ts`, `gui/postcss.config.cjs`, `gui/index.html`.
  - `gui/src/main.tsx`, `gui/src/App.tsx`, `gui/src/index.css` (tailwind base/components/utilities).
  - `gui/src/components/ui/` — shadcn-installed primitives: `button`, `accordion`, `badge`, `sheet`, `select`, `checkbox`, `toast`.
  - `gui/src-tauri/` — Tauri 2 Rust project.
    - `tauri.conf.json` — product name `u1kit`, bundle identifier `com.duncan.u1kit`, window: 1000×700 default, resizable.
    - `Cargo.toml` with `tauri = { version = "2", features = ["shell-open"] }`, `tauri-plugin-shell` for `Command`.
    - `src/main.rs` — default scaffold, register plugins.
    - `build.rs` — include resources.
- Create: `.github/workflows/gui-ci.yml` — matrix: windows-latest, macos-latest, ubuntu-latest. Steps: setup pnpm, install, `pnpm typecheck`, `pnpm lint`, `pnpm test --run`, `pnpm tauri build --debug` (smoke only, no release).
- Modify: `README.md` — add a `## GUI` section with quickstart (`cd gui && pnpm install && pnpm tauri dev`).
- Modify: `.gitignore` — add `gui/node_modules/`, `gui/dist/`, `gui/src-tauri/target/`, `gui/src-tauri/gen/`.

**Steps:**
1. `pnpm create tauri-app@latest gui --manager pnpm --template react-ts`. Select Tauri 2.
2. Install Tailwind: `pnpm -C gui add -D tailwindcss postcss autoprefixer && pnpm -C gui exec tailwindcss init -p`. Configure `tailwind.config.ts` content globs.
3. Initialize shadcn: `pnpm -C gui dlx shadcn@latest init`. Style: default, base color: slate, CSS variables: yes.
4. Add the 7 shadcn primitives listed above via `pnpm -C gui dlx shadcn@latest add button accordion badge sheet select checkbox toast`.
5. Write a trivial `App.tsx` that renders "u1kit" + a Button, proving the stack is wired.
6. Commit `.gitignore`, `README.md` GUI section, and the scaffold. CI must go green on all three OSes before the next task starts.
7. Gates (GUI-side only): `pnpm -C gui typecheck`, `pnpm -C gui lint`, `pnpm -C gui test --run` (no tests yet, but the command must succeed).
8. Commit: `feat(gui): Tauri 2 + React + Vite + Tailwind + shadcn scaffold`

**Test:** CI green on all three OSes. Local `pnpm tauri dev` shows a window with "u1kit".

---

## Task G3: Shared TypeScript types for CLI JSON contracts

**Why:** The CLI's JSON schema is the API. Mirroring it in TypeScript with zero drift is worth a dedicated task. All subsequent UI code consumes these types.

**Files:**
- Create: `gui/src/types/cli.ts` — TypeScript interfaces mirroring `u1kit/report.py`:
  - `Severity = "fail" | "warn" | "info"`
  - `Finding = { rule_id: string; severity: Severity; message: string; fixer_id: string | null; diff_preview: string | null; }`
  - `LintResponse = { schema_version: "1"; file: string; findings: Finding[]; }`
  - `FixerOutcome = { fixer_id: string; message: string; }`
  - `FixerSkip = { fixer_id: string; reason: string; }`
  - `FixResponse = { schema_version: "1"; file: string; preset: string; applied: FixerOutcome[]; skipped: FixerSkip[]; output_path: string; }`
  - `PresetEntry = { name: string; source: "builtin" | "user"; rules: string[]; }`
  - `PresetsListResponse = { schema_version: "1"; presets: PresetEntry[]; }`
- Create: `gui/src/lib/cli.ts` — `runCli<T>(args: string[]): Promise<T>` wrapper over Tauri's `Command`. Invokes the sidecar (path resolved via `resolveResource`), captures stdout, parses JSON, validates `schema_version === "1"`, throws typed errors on mismatch.
- Create: `gui/src/lib/cli.test.ts` — Vitest unit test with a mocked `Command`. Covers success, schema-mismatch, malformed JSON, non-zero exit with findings (exit 1, still parseable), crash (exit 2).
- Modify: `gui/src-tauri/tauri.conf.json` — declare `resources/sidecar/*` so `resolveResource` works.
- Create: `gui/src-tauri/resources/sidecar/.gitkeep` — placeholder. Actual binaries drop here via G10.
- Create: `gui/scripts/validate-schema.mjs` — runs host's `u1kit lint fixture.3mf --json` and asserts the output parses as `LintResponse`. Run in CI.

**Steps:**
1. Write the interfaces exactly matching `u1kit/report.py`. Add a JSDoc comment pointing to that file.
2. Write `runCli`. Catch `Command` errors and wrap. Validate `schema_version`.
3. Write 5 vitest cases for `runCli`.
4. Wire the schema-validation script into CI (needs the sidecar binary from G1; bootstrap by building on the runner).
5. Commit: `feat(gui): typed CLI contract + Command wrapper`

**Test:** 5 Vitest cases, schema-validation CI step.

---

## Task G4: File drop-zone + file picker

**Why:** First user-visible surface. Accept a `.3mf` (or `.zip`), stage its path in app state, and enable the next step.

**Files:**
- Create: `gui/src/components/DropZone.tsx` — HTML5 drag-drop + fallback button that opens Tauri's `dialog.open({ filters: [{ name: '3MF', extensions: ['3mf', 'zip'] }] })`.
- Create: `gui/src/state/session.ts` — app reducer: `type Session = Idle | FileLoaded | Linting | ShowingFindings | Fixing | Done | Error`. Actions: `FILE_DROPPED`, `FILE_CLEARED`, `LINT_STARTED`, `LINT_SUCCEEDED`, `LINT_FAILED`, `FIX_STARTED`, `FIX_SUCCEEDED`, `FIX_FAILED`, `RESET`.
- Modify: `gui/src/App.tsx` — wire reducer via `useReducer`, render `DropZone` in `Idle`.
- Create: `gui/src/components/DropZone.test.tsx` — Vitest + React Testing Library. Test: dropping a `.3mf` dispatches `FILE_DROPPED`; dropping a `.pdf` dispatches a toast; clicking the picker button opens the dialog (mocked).
- Add shadcn primitives if not already: `toast` (already added in G2).

**Steps:**
1. Implement `DropZone`. Visual: large dashed border, file icon (lucide-react), text "Drop a .3mf here or click to browse".
2. Wire reducer, initial state `Idle`.
3. Drop a `.pdf` → toast "Only .3mf files are supported." No state transition.
4. Write 3 Vitest cases.
5. Commit: `feat(gui): drop-zone and file-picker with session reducer`

**Test:** 3 Vitest cases; manual check in `pnpm tauri dev`.

---

## Task G5: Lint view — findings grouped by severity

**Why:** First real integration with the sidecar. After file drop, trigger `runCli(['lint', filePath, '--json'])`, render findings.

**Files:**
- Create: `gui/src/components/LintView.tsx` — renders `Accordion` with three sections: `Failing ({count})`, `Warnings ({count})`, `Info ({count})`. Each section contains a list of `FindingRow` components (placeholder for G6).
- Modify: `gui/src/App.tsx` — on `FILE_DROPPED`, dispatch `LINT_STARTED`, call `runCli`, dispatch `LINT_SUCCEEDED(findings)` or `LINT_FAILED(error)`.
- Create: `gui/src/components/LintView.test.tsx` — with a canned `LintResponse`, renders three sections, open-by-default behavior, correct counts.
- Create: `gui/src/components/FindingRow.tsx` — minimal for now: rule_id + severity Badge + message. Expansion added in G6.

**Steps:**
1. Implement `LintView`. Default-open first non-empty group (G-iii).
2. Wire App.tsx to run `runCli` on FILE_DROPPED.
3. Show a spinner while `Linting`.
4. On error, display a friendly message + "Try another file" button.
5. Write 4 Vitest cases.
6. Commit: `feat(gui): lint view with findings grouped by severity`

**Test:** 4 Vitest cases; manual check with the real fixture.

---

## Task G6: Per-finding detail + rule doc sheet

**Why:** Expanding a finding should show the `diff_preview` and a "Why?" link opening bundled rule documentation.

**Files:**
- Modify: `gui/src/components/FindingRow.tsx` — expandable. Shows `diff_preview` in a `<pre>` with syntax-highlight (none in MVP, just monospace), plus checkbox "Include in fix" (disabled if `fixer_id === null`), plus "Why?" button.
- Create: `gui/src/components/RuleDocSheet.tsx` — shadcn `Sheet`, renders bundled markdown via `react-markdown`.
- Create: `gui/src/ruledocs/` — one `.md` file per rule, split from `u1kit — Rule & Fixer Spec (v0 draft).md`. Files named `a1.md`, `a2.md`, …, `f1.md`. Each contains the rule's spec paragraph verbatim plus a "Why this matters" sentence.
- Create: `gui/src/lib/ruledocs.ts` — synchronous map `{ [rule_id]: string }` built from `import.meta.glob('../ruledocs/*.md', { as: 'raw' })`.
- Create: `gui/scripts/split-ruledocs.mjs` — derives the per-rule markdown from the spec file. Run once; manually reviewed. Not re-run in CI.
- Modify: `gui/package.json` — add `react-markdown`.
- Create: `gui/src/components/FindingRow.test.tsx`, `gui/src/components/RuleDocSheet.test.tsx`.

**Steps:**
1. Run the split script once to seed `gui/src/ruledocs/*.md`. Commit the generated markdown (it's the source of truth now).
2. Implement `FindingRow` expansion. Default collapsed; click chevron to open. Checkbox default-checked when `fixer_id !== null` per G-v.
3. Implement `RuleDocSheet`. Opens on "Why?" click, rendered by `react-markdown`.
4. Write 6 Vitest cases.
5. Commit: `feat(gui): per-finding detail with diff preview and rule doc sheet`

**Test:** 6 Vitest cases; manual smoke.

---

## Task G7: Preset picker + apply-fix workflow

**Why:** Close the loop. User picks a preset, confirms selected findings, clicks "Apply fixes", the sidecar runs `fix --json`, results are shown.

**Files:**
- Modify: `gui/src/App.tsx` — fetch presets via `runCli(['presets', 'list', '--json'])` on startup; store in reducer.
- Create: `gui/src/components/PresetPicker.tsx` — shadcn `Select`, options grouped by `builtin` vs `user` (if any users presets exist). Default: `bambu-to-u1`.
- Create: `gui/src/components/FixActionBar.tsx` — sticky bottom bar with `[Preset dropdown] [Checked: N] [Apply fixes]`.
- Create: `gui/src/components/FixResultView.tsx` — shown in `Done` state. Lists `applied[]` and `skipped[]`, shows `output_path`, offers "Save as…" (G8).
- Modify: `gui/src/state/session.ts` — add fields to `ShowingFindings`: `presetName`, `checkedFixerIds: Set<string>`.

**Steps:**
1. On app mount, fetch presets, populate the picker.
2. Wire action bar: `onApply = () => runCli(['fix', filePath, '--preset', presetName, '--json', '--only', ...checkedFixerIds])`.
3. Handle `exit=0` success, `exit=1` partial (some skipped), `exit=2` crash.
4. Render `FixResultView`.
5. Write 5 Vitest cases covering picker population, checkbox toggling, apply dispatch, skipped handling.
6. Commit: `feat(gui): preset picker and apply-fix workflow`

**Test:** 5 Vitest cases; manual end-to-end with the fixture.

---

## Task G8: Save-as flow

**Why:** The fix wrote output to a temp or default location. Let the user choose where to save the result.

**Files:**
- Modify: `gui/src/components/FixResultView.tsx` — add "Save as…" button. Opens `dialog.save({ defaultPath: derive from input, filters: [{name: '3MF', extensions: ['3mf']}] })`. On confirm, copy the fix's `output_path` to the chosen location.
- Create: `gui/src-tauri/src/commands.rs` — Tauri command `copy_file(src: String, dst: String) -> Result<(), String>`. Uses `std::fs::copy`.
- Modify: `gui/src-tauri/src/main.rs` — register the command.
- Modify: `gui/src/lib/cli.ts` — expose `copyFile` wrapping the command.
- Create: `gui/src/components/FixResultView.test.tsx`.

**Steps:**
1. Write the Rust `copy_file` command. Unit test via `cargo test`.
2. Wire the React side. Default filename: `{input_stem}_u1.3mf` (G-vi).
3. Write 2 Vitest cases (success, user-cancels).
4. Commit: `feat(gui): save-as flow with atomic copy`

**Test:** 2 Vitest cases + 1 Rust unit test.

---

## Task G9: Error and edge handling

**Why:** Audit every sidecar call and UI path for failure modes. Replace generic "Something went wrong" with actionable messaging.

**Files:**
- Modify: `gui/src/lib/cli.ts` — extend error taxonomy: `CliNotFoundError`, `CliCrashedError`, `CliMalformedJsonError`, `CliSchemaMismatchError`, `CliTimeoutError` (hard cap at 60s per call in MVP).
- Modify: each view component — display the mapped error.
- Create: `gui/src/components/ErrorBoundary.tsx` — React error boundary for uncaught errors.
- Modify: `gui/src/App.tsx` — wrap in `ErrorBoundary`; log to `console.error` for dev and to a local log file via Tauri in release.
- Create: `gui/src/lib/cli.errors.test.ts` — 8 cases covering each error type + timeout + partial stdout (truncated JSON).
- Modify: `gui/src-tauri/src/main.rs` — log-plugin config for release builds.

**Steps:**
1. Enumerate all sidecar call sites; wrap in typed catches.
2. Write the boundary component.
3. 8 Vitest cases.
4. Manual: kill the sidecar mid-run, corrupt a `.3mf` (remove `Metadata/project_settings.config`), feed a 0-byte file, rename the sidecar so it's missing — each should render a readable error.
5. Commit: `feat(gui): typed error taxonomy and React ErrorBoundary`

**Test:** 8 Vitest cases + manual fault injection.

---

## Task G10: Packaging per OS + CI matrix

**Why:** Ship a downloadable artifact on each OS. No signing/notarization (deferred to Phase 4), but the bundle must install and launch cleanly.

**Files:**
- Modify: `.github/workflows/gui-ci.yml` — add a `release` job triggered on `v*` tags. Matrix: windows-latest (MSI), macos-latest (DMG, unsigned), ubuntu-latest (AppImage + deb).
  - Each runner first builds the sidecar via `scripts/build_sidecar.py`, copies to `gui/src-tauri/resources/sidecar/<target-triple>/`, then runs `pnpm -C gui tauri build`.
  - Uploads artifacts to the workflow run.
- Modify: `gui/src-tauri/tauri.conf.json` — `bundle.resources: ["resources/sidecar/*"]`, `bundle.externalBin: []` (we're using resources, not externalBin, to keep path resolution consistent across dev/prod).
- Create: `docs/install.md` — one paragraph per OS. For macOS, include the "right-click → Open" unsigned-install path.
- Modify: `README.md` — link to `docs/install.md`.

**Steps:**
1. Wire the matrix. Test the release job via a `v0.0.0-rc1` tag on a feature branch.
2. Verify on each OS: install the artifact, launch, drop the `u1_native.3mf` fixture, click Apply, save — verify the saved file byte-identical to what the CLI produces directly.
3. Commit: `chore(release): packaging matrix and install docs`

**Test:** CI green on a release tag; manual install smoke on each OS if hardware is available.

---

## Task G11: End-to-end UX verification + Phase 3 exit

**Why:** The Phase 3 exit criterion is "non-technical user can drop a file, pick a preset, apply, and save without opening a terminal." One Playwright test asserts this flow holistically.

**Files:**
- Create: `gui/tests/e2e/happy-path.spec.ts` — Playwright test:
  1. Launch the Tauri app (via `@tauri-apps/cli`'s `tauri dev` in CI).
  2. Drop `tests/fixtures/real/u1_native.3mf` on the drop-zone.
  3. Wait for the Findings view.
  4. Select the `bambu-to-u1` preset (first item in the list).
  5. Click Apply.
  6. Wait for the Result view.
  7. Click Save as, choose a temp path, confirm.
  8. Assert the file exists at that path and its size matches the CLI's direct output.
- Modify: `.github/workflows/gui-ci.yml` — add a `e2e` job (Linux only for MVP; Tauri Playwright support on macOS/Windows is flaky).
- Modify: `gui/package.json` — add `@playwright/test`, `pnpm e2e` script.
- Create: `gui/playwright.config.ts`.
- Modify: `README.md` — mark Phase 3 as complete in the Status section; list the install link.

**Steps:**
1. Install Playwright.
2. Write the happy-path spec.
3. Add the e2e CI job.
4. Run full exit-criteria check (below).
5. Commit: `test(gui): end-to-end happy-path Playwright spec and Phase 3 exit`

**Test:** Playwright spec green in CI.

---

## Verification — Phase 2 wrap-up exit criteria

Run at the end of W4. All must pass:

- `pytest` — every rule has ≥1 test; every fixer has unit + idempotency tests.
- `mypy --strict u1kit/` — clean.
- `ruff check u1kit/ tests/` — clean.
- `u1kit lint tests/fixtures/real/u1_native.3mf --json` — `schema_version: "1"`, 0 fail-severity findings.
- `u1kit presets list` — shows all 5 starter presets + any user-dir presets, tagged by source.
- For each starter preset: `u1kit fix <appropriate-fixture> --preset <preset>` succeeds; output re-lints clean at the preset's targeted severities.
- `u1_native.3mf` round-trips byte-identical on non-config entries.
- `DECISIONS.md` — every Phase 2 open question is either resolved or has a "deferred to Phase 3" note.
- `README.md` — Status section reads "Phase 2: complete."

**Sanity check (not a blocker):** open one fixed file in Snapmaker Orca on a real machine if hardware is available.

---

## Verification — Phase 3 exit criteria

Run at the end of G11. All must pass:

- Every GUI task's unit tests green.
- `pnpm -C gui typecheck && pnpm -C gui lint && pnpm -C gui test --run` — clean.
- `pnpm -C gui tauri build` succeeds on each of Windows / macOS / Linux (CI matrix green).
- Playwright happy-path spec green on Linux CI.
- Schema-validation CI step confirms the CLI's `lint --json` output parses as `LintResponse`.
- Installable artifact per OS (unsigned, documented).
- `README.md` Status section reads "Phase 3: complete."
- Manual: a non-technical user (or anyone shown the app for the first time) can complete the flow drop → pick preset → apply → save without reading docs.

**Sanity check (not a blocker):** open the saved output in Snapmaker Orca and print.

---

## What's out of scope for this plan

**Phase 2 wrap-up out of scope:** new rules beyond E2/E3/F1, additional presets beyond the four named, GUI integration for any Phase 2 rule (Phase 3's job).

**Phase 3 out of scope (listed so the plan mode doesn't drift):**

- **Custom preset editor in the GUI** — bundled presets only in MVP. User-preset-directory presets are *listed* but not editable from the GUI. Create/edit still happens in a text editor at `platformdirs.user_config_path("u1kit") / "presets"`. Defer to a Phase 3.5 or Phase 4 task.
- **Settings screen** — default preset, default output location, CLI binary override. Out of scope for MVP. Defer.
- **Signing and notarization** — unsigned artifacts only. macOS users follow the right-click-Open workaround. Defer to Phase 4.
- **Auto-update** — no Tauri updater plugin in MVP. Manual re-download. Defer to Phase 4.
- **Telemetry** — none. No network calls from the GUI at all in MVP, aside from what React/Tauri do internally for the dev server.
- **i18n** — English only in MVP.
- **Svelte swap** — locked. Tauri + React is final for Phase 3.
- **Batch mode (`fix --batch DIR/`)** — Phase 4.
- **Watch-mode** — Phase 4.
- **Plugin discovery via entry points** — Phase 4.
- **Sanitizer CLI (`u1kit sanitize`)** — Phase 4.
- **Rule authoring docs** — Phase 4.
- **Homebrew / winget / AUR packaging** — Phase 4.
- **Accessibility audit (WCAG)** — basic keyboard navigation in G-viii is the MVP bar; full audit deferred.
- **Performance budget** — no target latency in MVP. The CLI is fast; the GUI inherits its speed.

---

## Task dependencies (for plan-mode's scheduling)

```
W0 → W1 → W4
W0 → W2 → W4
W0 → W3 → W4
W4 → G0
G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7 → G8 → G9 → G10 → G11
```

W1/W2/W3 can run in parallel after W0. The entire Phase 3 chain is linear: each task's artifact is the input to the next. G9 can start in parallel with G7/G8 once G5 lands, but the safer default is linear.
