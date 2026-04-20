# CLAUDE.md

Conventions and context for agents working on u1kit. Read this first.

## Project

`u1kit` is a Python CLI that converts Bambu/Makerworld `.3mf` files to run on
the Snapmaker U1 (a four-tool IDEX/toolchanger). It lints a `.3mf`, optionally
applies rule-specific fixers, and re-emits a byte-identical archive except for
the rewritten config entries.

The rule catalog, severities, and auto-fix semantics are defined in
`u1kit — Rule & Fixer Spec (v0 draft).md`. The phased plan lives in
`u1kit — Phased Development PRD draft 1.md` and the current phase's task list
lives in `phase-two.md`. All design decisions (Phase 1 + Phase 2) are in
`DECISIONS.md` — that file is the source of truth; if you're about to make a
judgment call that isn't already recorded there, add a new section rather than
burying the decision in a commit message.

## Repo layout

```
u1kit/
  archive.py       # .3mf read/write, non-config entries byte-identical
  bbl.py           # Bambu/U1 detection helpers (shared by B3 rule + fixer)
  cli.py           # Click entry point: lint / fix / presets list
  color.py         # CIEDE2000 distance (used by B1 interactive merge)
  config.py        # project_settings.config parse/emit
  filaments.py     # parallel-array accessor over filament fields
  geometry.py      # 3D/3dmodel.model XML parser (used by E-rules)
  interactive.py   # Click-based prompt + unified-diff preview
  mixed_blends.py  # semicolon-CSV parser for mixed_filament_definitions (D3)
  report.py        # text and JSON report formatting (schema_version "1")
  rules/           # one file per rule; subclasses of rules.base.Rule
  fixers/          # one file per fixer; subclasses of fixers.base.Fixer
  presets/         # YAML preset definitions (bambu-to-u1 shipped so far)
  data/            # u1_printer_reference.json, u1_toolchange.gcode
tests/
  fixtures/real/   # real .3mf corpus (starts with u1_native.3mf)
  test_*.py        # one file per module / subsystem
```

## Rule + fixer contract

Rules are pure functions wrapped in a class. Fixers mutate a working copy.

```python
# u1kit/rules/base.py
class Rule(ABC):
    @property @abstractmethod
    def id(self) -> str: ...             # e.g. "A2" — stable public identifier
    @property @abstractmethod
    def name(self) -> str: ...           # human-readable name
    @abstractmethod
    def check(self, context: Context) -> list[Result]: ...
    # Severity is set on each Result, not on the Rule — a single rule may
    # emit findings at different severities from the same check().

# u1kit/fixers/base.py
class Fixer(ABC):
    @property @abstractmethod
    def id(self) -> str: ...             # e.g. "a2" — matches rule_id.lower()
    def apply(self, config, filament_configs, context) -> None: ...
```

- Rule IDs are the public API. Presets reference them; user-visible
  `--only`/`--skip` flags will too. **Never rename a rule ID.**
- Fixer ID = lowercase rule ID.
- Every rule file is named `<id_lower>_<snake_description>.py` and exports a
  single class registered in `u1kit/rules/__init__.py`. Same pattern for fixers.
- Informational rules (A1, D3, E2, F1) have no fixer — their `Result` sets
  `fixer_id=None`.
- If a fixer refuses to apply (e.g. B1 without user consent), it raises a
  subclass of `FixerAbort`. The pipeline records a skipped `FixerResult`
  rather than crashing.
- Fixers must be **idempotent**. Every fixer has a unit test that applies it
  twice and asserts the second pass is a no-op. This is a hard Phase 2 exit
  criterion.

## Three gates

Every commit must pass all three. No exceptions.

```bash
pytest                       # 291+ tests, runs in <1s
mypy --strict u1kit/         # clean; 3.10 target
ruff check u1kit/ tests/     # clean; see pyproject.toml for selected rules
```

`from __future__ import annotations` at the top of every module — the project
targets Python 3.10+ but uses PEP 604 union syntax (`X | Y`).

## Dev install

```bash
pip install -e ".[dev]"
```

Runtime deps: `click`, `pyyaml`, `prompt-toolkit`, `platformdirs`. Dev deps
add `pytest`, `mypy`, `ruff`, `types-PyYAML`.

Note: if `mypy` segfaults, pin `mypy<1.15`. 1.20.1 has an unresolved issue on
this codebase in some environments.

## Commit policy

- One commit per task (Phase 2 uses the task numbering in `phase-two.md`).
- Subject line format: `feat(<area>): <description>` for new code,
  `test: <description>` for test-only commits, `docs: <description>` for docs,
  `chore: <description>` for housekeeping.
- Every commit passes the three gates locally before it lands.
- No squashing during a phase — the task-level history is the rollback unit.

## Line endings

`.gitattributes` enforces LF on all text files and marks `.3mf` / `.pyc` as
binary. If you see a whole-file diff on a Python or Markdown file, an editor
resaved it with CRLF — re-check out the file and make sure your editor's EOL
setting is LF.

## Archive fidelity

Non-config entries in the `.3mf` ZIP round-trip byte-identical: same
compression method, entry order, and mtimes. Rewritten config entries use
`ZIP_DEFLATED` with JSON serialized as `sort_keys=True, indent=4` plus a
trailing newline (matches Orca Slicer's observed output). This is verified
empirically against `tests/fixtures/real/u1_native.3mf` and must stay green.

## Where to look for answers

| Question | Read |
|---|---|
| "What does rule X do?" | `u1kit — Rule & Fixer Spec (v0 draft).md` |
| "Why did we pick value N for threshold Y?" | `DECISIONS.md` |
| "What's the current roadmap?" | `phase-three-plan.md` Progress table for the most recent completed phase; `u1kit — Phased Development PRD draft 1.md` §"Phase 4" for what's next |
| "How is `project_settings.config` shaped on U1 native?" | `DECISIONS.md` + the ground-truth table at the top of `phase-two.md` |
| "What's the JSON schema for `--json` output?" | `u1kit/report.py` — `schema_version: "1"` |
| "How does the interactive B1 merge work?" | `u1kit/interactive.py`, `u1kit/fixers/b1_filament_count.py`, and DECISIONS.md items 1–3 |

## Phase status (snapshot)

Phase 1 shipped. Phase 2 shipped — all 17 catalog rules (A1, A2, A3, B1–B5,
C1–C4, D1–D3, E1–E3, F1) and 13 fixers, plus five starter presets
(`bambu-to-u1`, `fs-uniform`, `peba-safe`, `plus-peba-multi`,
`makerworld-import`). Phase 3 shipped — Tauri 2 + React + Vite + Tailwind +
shadcn desktop GUI in `gui/` wrapping the CLI as a PyInstaller sidecar, with
the happy path (drop → lint → pick preset → apply → save-as) green end-to-end
and unsigned install artifacts (MSI/DMG/AppImage/deb) produced by
`.github/workflows/release.yml`. See `phase-three-plan.md` for the executed
task breakdown and `docs/install.md` for install instructions.

Next: Phase 4 — signing and notarization, auto-update, batch/watch CLI modes,
and wider distribution (Homebrew / winget / AUR). Not scoped yet; see
`u1kit — Phased Development PRD draft 1.md` §"Phase 4" for the rough outline.
