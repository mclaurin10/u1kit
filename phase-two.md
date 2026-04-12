# u1kit Phase 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Ship every remaining v0 rule (B1 interactive, B4, B5, C1–C4, D2, D3, E1–E3, F1), the four starter presets (`peba-safe`, `plus-peba-multi`, `fs-uniform`, `makerworld-import`), a user-preset-directory loader, and a minimal interactive UX layer on top of the Phase 1 Rule/Fixer architecture.

**Architecture:** Extend Phase 1's class-based Rule/Fixer pattern with a lean `u1kit/filaments.py` accessor over the flat parallel-array shape already used in `project_settings.config`. Add a stdlib-only interactive UX module (Click-confirm + `difflib.unified_diff`), a cross-platform user preset dir loader, and a CIEDE2000-based B1 merge. Every other Phase 2 rule plugs into the existing Pipeline unchanged.

**Tech stack:** Python 3.10+, Click, PyYAML, stdlib-only for diff/XML/color math. No prompt_toolkit (deferred to Phase 3 GUI). mypy --strict, ruff clean, `from __future__ import annotations` everywhere. Class-based Rule/Fixer subclasses registered in `u1kit/rules/__init__.py` / `u1kit/fixers/__init__.py`. Short-form fixer IDs == rule ID lowercased.

---

## Context

Phase 1 shipped 7 rules + 5 fixers and the `bambu-to-u1` preset, with a Pipeline that supports dry-run / auto / interactive modes and a byte-identical archive round-trip. Phase 2 completes the v0 rule catalog: it delivers the 13 deferred rules, four additional starter presets, user-defined preset loading, and a diff-preview-capable interactive UX. With Phase 2 done, every rule the spec anticipated has a fixture test, and all five presets are runnable end-to-end — unblocking the Phase 3 Tauri GUI, which talks to the CLI over `--json` and never needs its own rule engine.

**Open DECISIONS.md items this phase must resolve:**
1. Archive fidelity vs. Snapmaker Orca (DECISIONS.md:5–13). A real file (`u1.3mf`) is now in the repo root; T1 consumes it.
2. Filament-config location ambiguity (DECISIONS.md:102–108). Ground truth from `u1.3mf` says *flat parallel arrays inside `project_settings.config`*; Phase 1 already accidentally made the right call. T2 resolves the note.

---

## Ground truth from `u1.3mf` (Snapmaker Orca native export, 2025-12-13 template)

These are **facts**, not guesses, extracted by unzipping the file and reading `Metadata/project_settings.config`. They dissolve half the Rule & Fixer Spec's ambiguities.

| Key | Shape on U1 native | Phase 2 rule(s) that need it |
|---|---|---|
| `filament_type` | `['PLA', 'PLA', 'TPU', 'TPU']` — one per filament slot | B4, B5, C1-C4, D3, F1 |
| `filament_colour` | `['#003776', '#2D9E59', '#A8F20D', '#FF3C3C']` — hex strings | B1 |
| `filament_max_volumetric_speed` | `['20', '20', '5', '5']` — parallel array | B4 |
| `filament_settings_id` | `['Generic PLA @Snapmaker U1', ...]` — profile `@` printer lineage | F1 |
| `filament_ids` | `['', '', '', '']` — **empty on native export**, cannot use for F1 | F1 |
| `filament_is_support` | `['0', '0', '0', '0']` — per-filament flag | B5 (support-eligibility) |
| `hot_plate_temp` | `['50', '50', '50', '50']` — **per-filament** bed temp, not per-plate | C1 |
| `textured_plate_temp` | `['55', '55', '55', '55']` — same | C1 |
| `hot_plate_temp_initial_layer` | `['50', '50', '50', '50']` — what the spec calls `first_layer_bed_temperature` | C2 |
| `textured_plate_temp_initial_layer` | parallel array | C2 |
| `slow_down_layer_time` | `['4', '4', '12', '12']` — PEBA's 12s next to PLA's 4s, spec example verified | C3 |
| `fan_max_speed` / `fan_min_speed` | parallel arrays | C4 |
| `z_hop` | `['0.4', '0.4', '0.4', '0.4']` — **first-class numeric**, per filament | D2 |
| `filament_z_hop` | `['0', '0', '0', '0']` — secondary override | D2 |
| `mixed_filament_definitions` | `"1,2,0,0,50,0,g,w,m2,d1,o1,u7;1,2,1,1,50,0,..."` — semicolon-CSV, ratio at pos 5 | D3 |
| `wall_filament`, `support_filament`, `support_interface_filament`, `sparse_infill_filament`, `solid_infill_filament`, `wipe_tower_filament` | `'1'` / `'2'` / ... — scalar **1-based** indices into the filament arrays | B1 (used-set), B5 |
| `first_layer_bed_temperature` | **not present** on this U1 native | C2 must handle absence gracefully |
| `curr_bed_type` | **not present** on this U1 native either | C1/C2 must not rely on it |

**Implications:**
- D2 does **not** need regex Z-hop extraction from `change_filament_gcode`. Use `z_hop` (primary) and `filament_z_hop` (override) directly.
- There is **no plate abstraction**. "Filaments sharing a plate" simply means "the used-set" — derived from `wall_filament` + `support_filament` + `*_infill_filament` etc. All bed-temp/cooling/fan fields are parallel to the full filament list.
- The Rule & Fixer Spec's C1/C2 wording of "≥2 filaments with different … share a plate" translates to "≥2 used filaments have different values in the parallel array".
- B5's "rigid alternative" check: `filament_type[int(support_filament) - 1] in FLEXIBLES` and some other filament is not flexible.
- F1's lineage heuristic: regex `@<printer>` suffix on `filament_settings_id[i]`. Empty suffix or foreign printer = flag.

---

## Spec ambiguities for DECISIONS.md (resolutions proposed; locked in T2)

Each of these must be recorded in DECISIONS.md before the task that touches it. Proposed resolutions in bold — to be confirmed during T2 and revisited per task if new evidence arrives.

1. **B1 color-distance metric** — RGB Euclidean / Lab ΔE / CIEDE2000?  
   **Proposed: CIEDE2000** (perceptually accurate, stdlib-implementable in <80 LoC, tested against reference values).
2. **B1 merge direction** — when merging filament *j* into filament *i*, which color wins?  
   **Proposed: the one whose index appears first in the used-set stays; the other's references are remapped to it.**
3. **B1 interactive UI** — PRD:50 says "CLI shows the proposed merge table and asks y/n".  
   **Proposed: one y/n per proposed merge, with an "all at once" shortcut. Rich editing deferred to Phase 3 GUI.**
4. **B4 line cross-section formula** — which `line_width`?  
   **Proposed: `outer_wall_line_width × layer_height` for the `outer_wall_speed` cap, same for the inner wall, `sparse_infill_line_width × layer_height` for infill. "Conservative factor" = 0.8 (documented).**
5. **B5 rigid alternative criterion** — which materials count as "rigid PLA"?  
   **Proposed: any filament whose `filament_type ∈ {PLA, PETG, ABS, ASA, PC}` and whose index is not already the flexible one. Prefer PLA; fall back alphabetically.**
6. **C1/C2 "share a plate"** — resolved by ground truth above. **Ship: used-set + parallel array**. No plate abstraction.
7. **C2 safe textured-PEI first-layer cap** — spec says "cap at safe textured-PEI range" but no number.  
   **Proposed: 65°C** (matches the spec's own trigger condition; documented in DECISIONS.md).
8. **C2 `first_layer_bed_temperature` absence** — the canonical field isn't on U1 native.  
   **Proposed: C2 operates on whichever `*_plate_temp_initial_layer` array the config actually contains, falling back to `hot_plate_temp_initial_layer`. If none present, C2 emits no Result.**
9. **D2 Z-hop primary source** — `z_hop` vs `filament_z_hop`?  
   **Proposed: flag if `max(z_hop[i], filament_z_hop[i]) ≥ 5 × layer_height` for any used filament. Fix writes the capped value back to `z_hop[i]` and zeroes `filament_z_hop[i]` to avoid the override.**
10. **D3 toolchange estimate formula** — spec says "surface estimated toolchange count" with no formula.  
    **Proposed: `layer_count × #mixed_definitions_with_ratio_50` (≈ one toolchange per layer per 1:1 blend). Informational only — exact count doesn't matter; order of magnitude does.**
11. **E1 thinnest-feature detection** — spec says "parse object dimensions, estimate thinnest feature".  
    **Proposed: take the minimum of the object's bounding-box dimensions (from `3D/3dmodel.model` XML). True mesh analysis is out of scope; bounding-box min is a safe lower bound for warn-level guidance.**
12. **E1 `line_width` choice** — which?  
    **Proposed: `outer_wall_line_width`** (the tightest constraint in practice).
13. **E2 volumetric speed** — per-filament arrays; which value?  
    **Proposed: minimum across the used-set** (the slowest filament dominates).
14. **E3 plate-size threshold** — spec literally says "below some threshold".  
    **Proposed: 120 × 120 mm** (roughly half the U1 bed; documented; make it tunable via preset option).
15. **E3 prime tower brim bump** — spec says "suggest bumping". No target value.  
    **Proposed: `max(current_prime_tower_brim_width, 5)` mm** (warn-level; auto-fix optional).
16. **F1 lineage heuristic** — what's "proper filament_settings_id lineage"?  
    **Proposed: regex `r" @[A-Za-z0-9 ]+$"` on each used filament's `filament_settings_id`. If the suffix is missing or doesn't match `@Snapmaker U1`, emit info. Matches the U1 native pattern observed.**
17. **Interactive UX — Click vs prompt_toolkit** — PRD:20 says "or equivalent".  
    **Proposed: Click only**, using `click.confirm()` + `click.prompt()` + `difflib.unified_diff`. Prompt_toolkit is reserved for Phase 3 GUI. Rationale: no new dependency, CliRunner tests stay simple.
18. **User preset dir on Windows** — `~/.config/u1kit/presets/` is POSIX only.  
    **Proposed: use `platformdirs.user_config_path("u1kit") / "presets"`**. New dep `platformdirs ≥ 3`.
19. **Archive fidelity vs real file** — DECISIONS.md:5–13 is unverified.  
    **T1 resolves this empirically** by round-tripping `u1.3mf` and asserting byte-identical output. If the round-trip breaks, fix `archive.py` before proceeding.
20. **Fixture corpus** — Phase 1 used only synthesized dicts. Phase 2 should have real artifacts.  
    **Proposed: `tests/fixtures/real/u1_native.3mf`** is the starting point. Add Bambu/Makerworld/FS samples as they become available. Don't block Phase 2 on corpus completeness.

These resolutions are proposals. T2 locks them into DECISIONS.md; subsequent tasks may revise individual entries if the implementation surfaces counterevidence, but must update DECISIONS.md in the same commit.

---

## Commit policy

- One commit per task. Commit message format: `feat(<area>): <short description>` for new code, `test: <description>` for test-only tasks, `docs: <description>` for docs-only tasks, `chore: <description>` for housekeeping.
- Every commit passes: `pytest`, `mypy --strict u1kit/`, `ruff check u1kit/ tests/`.
- No squash commits during Phase 2; we want the task-level history for rollback.
- Task 0 (the spec-docs commit) is the **first** Phase 2 commit by convention — per the user's explicit instruction that the PRD and Rule & Fixer Spec live in git, not a chat sidebar.

---

## Tasks

### Task 0: Commit Phase 2 spec docs into the repo

**Why:** PRD and Rule & Fixer Spec are currently in the repo tree but untracked. They must live in git alongside `README.md` and `DECISIONS.md` as durable project docs (user requirement).

**Files:**
- Create: `phase-two.md` — this plan, copied from the planning scratch file.
- Track: `u1kit — Phased Development PRD draft 1.md` (already in tree, needs `git add`)
- Track: `u1kit — Rule & Fixer Spec (v0 draft).md` (already in tree, needs `git add`)

**Steps:**
1. Verify files exist in project root via `ls -la "C:/Dev/u1kit/" | grep -iE 'prd|spec|phase-two'`.
2. `git add "u1kit — Phased Development PRD draft 1.md" "u1kit — Rule & Fixer Spec (v0 draft).md" phase-two.md`
3. Commit: `docs: import Phase 2 PRD, Rule & Fixer Spec, and implementation plan`

**No test.** This is a docs-only task.

---

### Task 1: Real-file fixture harvest + archive fidelity verification

**Why:** DECISIONS.md:5–13 flags archive round-trip fidelity as unverified against a real Snapmaker Orca export. We have `u1.3mf` at the repo root; move it to the test fixtures directory and write a round-trip test that confirms byte-identical output. Phase 1 shipped with synthesized-dict-only fixtures; this task starts the real-fixture corpus.

**Files:**
- Create: `tests/fixtures/real/u1_native.3mf` (moved from `C:/Dev/u1kit/u1.3mf`)
- Create: `tests/fixtures/real/__init__.py` (empty, makes it package-discoverable)
- Modify: `tests/conftest.py` — add fixture `u1_native_3mf_path` returning the path, and `u1_native_3mf_bytes` returning its bytes.
- Modify: `tests/test_archive_roundtrip.py` — add `TestRealFileRoundtrip::test_u1_native_byte_identical`.
- Modify: `DECISIONS.md` — resolve the "Archive fidelity" open question.

**Step 1: Write the failing test**

In `tests/test_archive_roundtrip.py`:
```python
class TestRealFileRoundtrip:
    def test_u1_native_roundtrip_preserves_bytes(
        self, u1_native_3mf_bytes: bytes
    ) -> None:
        archive = read_3mf(io.BytesIO(u1_native_3mf_bytes))
        out = io.BytesIO()
        write_3mf(archive, out)
        # Non-config entries must be byte-identical.
        original = zipfile.ZipFile(io.BytesIO(u1_native_3mf_bytes))
        rewritten = zipfile.ZipFile(io.BytesIO(out.getvalue()))
        non_config = [
            n for n in original.namelist()
            if not (n.endswith(".config") and n.startswith("Metadata/"))
        ]
        for name in non_config:
            assert original.read(name) == rewritten.read(name), (
                f"{name}: content changed on round-trip"
            )
```

**Step 2: Run test → expect FAIL** with "fixture `u1_native_3mf_bytes` not found".

**Step 3: Add fixture and move file.**
- `git mv u1.3mf tests/fixtures/real/u1_native.3mf` (if already tracked; else `mv` and `git add`)
- In `tests/conftest.py`:
  ```python
  @pytest.fixture
  def u1_native_3mf_path() -> Path:
      return Path(__file__).parent / "fixtures" / "real" / "u1_native.3mf"

  @pytest.fixture
  def u1_native_3mf_bytes(u1_native_3mf_path: Path) -> bytes:
      return u1_native_3mf_path.read_bytes()
  ```

**Step 4: Run test → expect PASS** (or investigate if `archive.py` breaks on the real file).

**Step 5: Update DECISIONS.md** — replace the "Open question: Whether Snapmaker Orca cares…" note with "**Resolved 2026-04-XX:** round-trip against `tests/fixtures/real/u1_native.3mf` passes byte-identical on non-config entries. See `tests/test_archive_roundtrip.py::TestRealFileRoundtrip::test_u1_native_roundtrip_preserves_bytes`."

**Step 6: Commit** — `test: real-file archive fidelity verified against u1.3mf`

---

### Task 2: Lock Phase 2 open questions and ground-truth into DECISIONS.md

**Why:** The 20 resolutions listed above must be durable. Every subsequent task assumes them; if any is wrong, the task that hits the counterevidence must update DECISIONS.md in the same commit.

**Files:**
- Modify: `DECISIONS.md` — append a `## Phase 2 open questions` section containing the 20 entries from this plan (or shortened references to the plan itself for the ones with concrete formulas).
- Modify: `DECISIONS.md` — update the "Filament config location" entry to reflect ground truth: *"Verified 2026-04-XX against `u1.3mf`: filament fields are flat parallel arrays on `project_settings.config`. There are no per-plate filament configs on Snapmaker Orca native exports. Phase 1's pragmatic choice was correct."*

**No test.** Docs-only.

**Commit:** `docs: Phase 2 open questions + ground-truth resolutions`

---

### Task 3: `u1kit/filaments.py` — parallel-array accessor

**Why:** B1, B4, B5, C1, C2, C3, C4, D2, D3, F1 all need to walk the per-filament parallel arrays in `project_settings.config`. Centralizing access in one module avoids ten copies of the same "parse scalar-or-list-or-int" code and gives a single place to fix bugs.

**Files:**
- Create: `u1kit/filaments.py`
- Create: `tests/test_filaments.py`

**API to implement:**
```python
from __future__ import annotations
from typing import Any, Iterable

FLEXIBLE_TYPES = frozenset({"TPU", "PEBA", "TPE"})
RIGID_PREFERRED = ("PLA", "PETG", "ABS", "ASA", "PC")

def get_filament_count(config: dict[str, Any]) -> int:
    """Return the number of filament slots. Uses `filament_colour` length."""

def get_filament_field(config: dict[str, Any], field: str, index: int) -> str | None:
    """Return the value at the given slot index for a parallel array field.
    Returns None if the field is absent or the array is shorter than index+1."""

def get_used_filament_indices(config: dict[str, Any]) -> list[int]:
    """Return the 0-based indices of filaments referenced by wall/support/
    infill/wipe-tower selectors. Deduplicated, sorted. Empty (0) is ignored."""

def is_flexible(filament_type: str | None) -> bool:
    """True if filament_type is in FLEXIBLE_TYPES (case-insensitive)."""

def find_rigid_alternative(
    config: dict[str, Any], exclude_index: int
) -> int | None:
    """Return the 0-based index of a non-flexible filament other than
    exclude_index, preferring RIGID_PREFERRED order. None if no alternative."""

def parse_scalar_index(value: Any) -> int | None:
    """Parse a scalar filament selector ('1', 1, '0') to a 0-based index.
    Returns None if 0/empty (meaning 'unset')."""
```

**Step 1: Write failing tests** in `tests/test_filaments.py`:
```python
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

class TestIsFlexible:
    @pytest.mark.parametrize("value,expected", [
        ("TPU", True), ("tpu", True), ("PEBA", True),
        ("PLA", False), ("", False), (None, False),
    ])
    def test_classifies_flex(self, value: str | None, expected: bool) -> None:
        assert is_flexible(value) is expected

class TestFindRigidAlternative:
    def test_prefers_pla(self) -> None:
        config = {
            "filament_type": ["TPU", "PLA", "PETG", "TPU"],
            "filament_colour": ["#0", "#1", "#2", "#3"],
        }
        assert find_rigid_alternative(config, exclude_index=0) == 1

    def test_none_when_all_flex(self) -> None:
        config = {
            "filament_type": ["TPU", "PEBA"],
            "filament_colour": ["#0", "#1"],
        }
        assert find_rigid_alternative(config, exclude_index=0) is None
```

**Step 2:** Run → FAIL (module missing).

**Step 3:** Implement `u1kit/filaments.py` with the API above.

**Step 4:** Run → PASS.

**Step 5:** Commit — `feat(filaments): parallel-array accessor for Phase 2 rules`

---

### Task 4: Interactive UX module + unified-diff rendering

**Why:** The Phase 1 `_interactive_prompt` in `u1kit/cli.py:216-221` is inline and untested. Phase 2 needs a proper module with: (a) accept/skip decision, (b) unified-diff rendering of `diff_preview`, (c) an `edit` callback hook for B1 (the only Phase 2 rule that needs custom interactive input). Stay on Click; no prompt_toolkit.

**Files:**
- Create: `u1kit/interactive.py`
- Create: `tests/test_interactive.py`
- Modify: `u1kit/cli.py` — replace `_interactive_prompt` with the new module's `prompt_fix`.
- Modify: `u1kit/fixers/base.py` — add optional `EditCallback = Callable[[Result, Fixer], bool]` parameter to `Pipeline.__init__` (already there as `interactive_callback`; keep name, just extend contract docstring).

**API:**
```python
from __future__ import annotations
import difflib
from enum import Enum
from typing import Callable, Protocol

import click

from u1kit.rules.base import Result
from u1kit.fixers.base import Fixer


class FixAction(Enum):
    APPLY = "apply"
    SKIP = "skip"
    QUIT = "quit"


class EditHook(Protocol):
    """Optional per-fixer editor. Returns True to apply, False to skip."""
    def __call__(self, result: Result, fixer: Fixer) -> bool: ...


def render_diff_preview(diff_preview: str | None) -> str:
    """Render a Result.diff_preview as a unified-diff-style block.
    If the preview already contains '->' pairs (Phase 1 style), reformat
    them as a 2-column diff. If it's plain text, return as-is with a
    `diff --` header."""

def prompt_fix(
    result: Result,
    fixer: Fixer,
    edit_hook: EditHook | None = None,
) -> FixAction:
    """Render the finding + preview, offer [a]pply/[s]kip/[q]uit (plus [e]dit
    if edit_hook is provided). Returns the chosen FixAction."""
```

**Step 1: Failing test**
```python
class TestPromptFix:
    def test_accept_returns_apply(self, monkeypatch) -> None:
        result = Result(
            rule_id="A2", severity=Severity.FAIL, message="profile wrong",
            fixer_id="a2", diff_preview="foo -> bar",
        )
        monkeypatch.setattr("click.prompt", lambda *a, **k: "a")
        action = prompt_fix(result, _DummyFixer(id="a2"))
        assert action is FixAction.APPLY

    def test_skip_returns_skip(self, monkeypatch) -> None:
        monkeypatch.setattr("click.prompt", lambda *a, **k: "s")
        action = prompt_fix(result_fixture(), _DummyFixer(id="a2"))
        assert action is FixAction.SKIP

class TestRenderDiffPreview:
    def test_arrow_style_becomes_two_column(self) -> None:
        out = render_diff_preview("printer_settings_id: 'Bambu' -> 'U1'")
        assert "-" in out and "+" in out
        assert "Bambu" in out and "U1" in out

    def test_none_returns_empty(self) -> None:
        assert render_diff_preview(None) == ""
```

**Step 2:** Run → FAIL.

**Step 3:** Implement `u1kit/interactive.py`. For `render_diff_preview`, split `diff_preview` lines on ` -> `, emit `- <before>` / `+ <after>` pairs. For `prompt_fix`, use `click.echo` for the finding header, `render_diff_preview` for the body, `click.prompt` with `type=click.Choice(['a', 's', 'q'])` (plus `'e'` if `edit_hook`).

**Step 4:** Run → PASS.

**Step 5:** Update `u1kit/cli.py:216–221`:
```python
from u1kit.interactive import FixAction, prompt_fix

def _interactive_callback(result: Result, fixer: Fixer) -> bool:
    action = prompt_fix(result, fixer)
    if action is FixAction.QUIT:
        raise click.Abort()
    return action is FixAction.APPLY
```

**Step 6:** Re-run full test suite; existing CLI tests should still pass (they use `runner.invoke(..., input="y\n")` which Click's confirm handles; new tests use the `a/s/q` choice). Update `tests/test_cli.py` to feed `"a\n"` instead of `"y\n"` for interactive fixer tests if any break.

**Step 7:** Commit — `feat(interactive): extract prompt module with unified-diff preview`

---

### Task 5: User preset directory loader

**Why:** PRD:19 requires "user-defined preset loading from `~/.config/u1kit/presets/`". On Windows that path is wrong; use `platformdirs` to get a cross-platform config dir.

**Files:**
- Modify: `pyproject.toml` — add `platformdirs>=3.0` to dependencies
- Modify: `u1kit/cli.py` — update `_load_preset` and `_list_presets` to search user dir first, then bundled
- Create: `tests/test_preset_loader.py` (or extend existing preset tests in `tests/test_cli.py`)

**Step 1: Failing test**
```python
class TestUserPresetLoader:
    def test_user_preset_overrides_bundled(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "my-preset.yaml").write_text(
            "name: my-preset\ndescription: user-defined\nrules: [A2]\n"
        )
        monkeypatch.setattr(
            "u1kit.cli._user_preset_dir", lambda: user_dir
        )
        data = _load_preset("my-preset")
        assert data["description"] == "user-defined"

    def test_presets_list_tags_source(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        user_dir = tmp_path / "presets"
        user_dir.mkdir()
        (user_dir / "custom.yaml").write_text(
            "name: custom\ndescription: x\nrules: [A2]\n"
        )
        monkeypatch.setattr(
            "u1kit.cli._user_preset_dir", lambda: user_dir
        )
        runner = CliRunner()
        result = runner.invoke(main, ["presets", "list"])
        assert result.exit_code == 0
        assert "bundled" in result.output
        assert "user" in result.output
        assert "custom" in result.output
```

**Step 2:** Run → FAIL.

**Step 3:** Implement:
```python
# u1kit/cli.py
from platformdirs import user_config_path

def _user_preset_dir() -> Path:
    return user_config_path("u1kit") / "presets"

def _load_preset(name: str) -> dict[str, Any]:
    # 1. Search user dir
    user_dir = _user_preset_dir()
    if user_dir.is_dir():
        for filename in (f"{name}.yaml", f"{name.replace('-', '_')}.yaml"):
            path = user_dir / filename
            if path.exists():
                return yaml.safe_load(path.read_text(encoding="utf-8"))
    # 2. Fall back to bundled (existing logic)
    ...

def _list_presets() -> list[tuple[str, dict[str, Any], str]]:
    """Return [(name, data, source)] where source is 'bundled' or 'user'."""
```

Update `presets_list` command to render the source tag in both human and JSON output.

**Step 4:** Run → PASS.

**Step 5:** Commit — `feat(cli): user-defined preset loading from platformdirs config dir`

---

### Task 6: `u1kit/color.py` — CIEDE2000 distance

**Why:** B1's merge strategy is "merge closest pair by color distance" (spec:8). Pure-math module; testable against known reference values (Sharma et al. 2005 test vectors).

**Files:**
- Create: `u1kit/color.py`
- Create: `tests/test_color.py`

**API:**
```python
def hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """'#003776' -> (0.0, 55.0, 118.0) in 0-255."""

def rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """sRGB → CIE Lab using D65 reference white."""

def ciede2000(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
    """CIEDE2000 perceptual color difference. See Sharma et al. 2005."""

def hex_distance(hex_a: str, hex_b: str) -> float:
    """Shortcut: hex_a → Lab, hex_b → Lab, CIEDE2000 distance."""
```

**Step 1: Failing tests** using Sharma's reference pairs:
```python
@pytest.mark.parametrize("lab1,lab2,expected", [
    ((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
    ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
    # ... up to the full Sharma table (34 pairs)
])
def test_ciede2000_matches_sharma_reference(
    lab1: tuple, lab2: tuple, expected: float
) -> None:
    assert ciede2000(lab1, lab2) == pytest.approx(expected, abs=1e-4)

def test_hex_distance_identical_colors_is_zero() -> None:
    assert hex_distance("#FF0000", "#FF0000") == pytest.approx(0.0, abs=1e-6)

def test_hex_distance_red_vs_green_is_large() -> None:
    assert hex_distance("#FF0000", "#00FF00") > 80
```

**Step 2:** Run → FAIL.

**Step 3:** Implement `u1kit/color.py`. Use stdlib-only (no numpy). Reference: https://en.wikipedia.org/wiki/Color_difference#CIEDE2000 — port the formula. Roughly 70 LoC.

**Step 4:** Run → PASS.

**Step 5:** Commit — `feat(color): CIEDE2000 distance for B1 filament merge`

---

### Task 7: B1 interactive filament-merge fixer

**Why:** Phase 1 B1 is report-only. Phase 2 adds the fixer, which in interactive mode shows a proposed merge table (smallest color distance first) and asks y/n per merge.

**Files:**
- Create: `u1kit/fixers/b1_filament_count.py`
- Modify: `u1kit/rules/b1_filament_count.py` — set `fixer_id="b1"` on the failing Result
- Modify: `u1kit/fixers/__init__.py` — register `B1FilamentCountFixer`
- Create: `tests/test_b1_fixer.py`
- Modify: `tests/test_rules.py::TestB1FilamentCount` — update assertion to `fixer_id == "b1"`

**Behavior:**
- Input: config with >4 filaments.
- Algorithm: repeatedly find the pair with smallest CIEDE2000 distance; merge the higher-index filament into the lower-index. Remap all selectors (`wall_filament`, `support_filament`, etc.) and all parallel filament arrays. Continue until ≤4 remain.
- **Interactive mode:** per merge, show a table row:
  ```
  Merge filament 5 (#FF00FF, PLA) → filament 3 (#FF0000, PLA)   ΔE=18.2
    Affected selectors: sparse_infill_filament
  Apply this merge? [a/s/q]:
  ```
- **Non-interactive mode (AUTO):** refuse. Emit an error Result saying "B1 merge requires --interactive or explicit consent; refusing to auto-merge filaments".

**Step 1: Failing test**
```python
class TestB1Fixer:
    def test_merges_closest_pair(self) -> None:
        # 5 filaments, two nearly-identical reds
        config = {
            "filament_colour": ["#FF0000", "#FE0000", "#00FF00", "#0000FF", "#FFFF00"],
            "filament_type": ["PLA", "PLA", "PLA", "PLA", "PLA"],
            "wall_filament": "1",
            "sparse_infill_filament": "2",  # points at the one being merged
            "filament_settings_id": ["A", "B", "C", "D", "E"],
        }
        fixer = B1FilamentCountFixer()
        ctx = Context(config=config, options={"b1_interactive": False, "b1_force_merge": True})
        fixer.apply(config, {}, ctx)
        assert len(config["filament_colour"]) == 4
        # sparse_infill_filament was 2 (index 1); merged into 1 (index 0)
        assert config["sparse_infill_filament"] == "1"

    def test_refuses_without_force_or_interactive(self) -> None:
        config = {"filament_colour": ["#1", "#2", "#3", "#4", "#5"], "filament_type": ["PLA"]*5}
        fixer = B1FilamentCountFixer()
        ctx = Context(config=config)
        with pytest.raises(B1MergeRequiresConsent):
            fixer.apply(config, {}, ctx)

    def test_interactive_accepts_via_callback(
        self, monkeypatch
    ) -> None:
        monkeypatch.setattr("u1kit.interactive.prompt_fix", lambda *a, **k: FixAction.APPLY)
        config = {"filament_colour": ["#1", "#2", "#3", "#4", "#5"], "filament_type": ["PLA"]*5}
        fixer = B1FilamentCountFixer()
        ctx = Context(config=config, options={"b1_interactive": True})
        fixer.apply(config, {}, ctx)
        assert len(config["filament_colour"]) == 4

class TestB1Idempotent:
    def test_b1_idempotent(self) -> None:
        config = {...}
        fixer = B1FilamentCountFixer()
        ctx = Context(config=config, options={"b1_force_merge": True})
        fixer.apply(config, {}, ctx)
        snapshot = copy.deepcopy(config)
        fixer.apply(config, {}, ctx)
        assert config == snapshot  # Already at 4, no further merge
```

**Step 2:** Run → FAIL.

**Step 3:** Implement. Core algorithm in a helper `_merge_filaments(config, src_idx, dst_idx)` that:
- For every parallel array field in config whose length matches `filament_count`, pop index `src_idx`
- For every scalar selector field, if it points at `src_idx+1`, remap to `dst_idx+1`; if it points at an index higher than `src_idx+1`, decrement by 1
- Filament list fields to enumerate: use `get_filament_count` from `filaments.py` to detect which keys are parallel.

**Step 4:** Run → PASS.

**Step 5:** Update `u1kit/rules/b1_filament_count.py` to emit `fixer_id="b1"` (was `None`). Update `tests/test_rules.py::TestB1FilamentCount::test_5_filaments_fails` assertion.

**Step 6:** Run full test suite.

**Step 7:** Commit — `feat(b1): interactive filament-merge fixer with CIEDE2000 selection`

---

### Task 8: B4 (flexibles speed caps) + B5 (flexible-as-support swap)

**Why:** Both rules operate on `filament_type` + per-filament fields and share the flexibility classifier from `filaments.py`. Batching them into one task reduces registration overhead and keeps shared test fixtures close together.

**Files:**
- Create: `u1kit/rules/b4_flexible_speed_caps.py`
- Create: `u1kit/fixers/b4_flexible_speed_caps.py`
- Create: `u1kit/rules/b5_flexible_support.py`
- Create: `u1kit/fixers/b5_flexible_support.py`
- Modify: `u1kit/rules/__init__.py`, `u1kit/fixers/__init__.py` — register all four
- Modify: `tests/test_rules.py`, `tests/test_fixers.py` — add `TestB4FlexibleSpeedCaps`, `TestB4Fixer`, `TestB5FlexibleSupport`, `TestB5Fixer`
- Modify: `tests/conftest.py` — add `make_tpu_config()` helper

**B4 behavior:**
- Trigger: any used filament has `filament_type ∈ FLEXIBLE_TYPES` AND lacks a per-filament speed cap.
- "Lacks a per-filament speed cap" = missing or nil entry in `filament_max_volumetric_speed`, OR missing per-filament overrides on `outer_wall_speed` / `inner_wall_speed` / `sparse_infill_speed` for that slot.
- Fix: compute `max_vol_speed / (line_width × layer_height) × 0.8` and inject as per-filament override. Currently u1.3mf stores these as global scalars; B4 introduces per-filament arrays in place (or populates the existing filament slot arrays if present).

**B5 behavior:**
- Trigger: `support_filament` or `support_interface_filament` points at a flexible filament.
- Fix: `find_rigid_alternative(config, exclude_index=flex_idx)`; if found, reassign both selectors. Else warn-only.

**Step 1: Failing tests**

B4:
```python
class TestB4FlexibleSpeedCaps:
    def test_tpu_without_caps_fails_warn(self) -> None:
        config = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#0", "#1"],
            "filament_max_volumetric_speed": ["20", "5"],
            "wall_filament": "2",
            "outer_wall_line_width": "0.42",
            "layer_height": "0.2",
            # note: no per-filament speed overrides
        }
        results = B4FlexibleSpeedCaps().check(Context(config=config))
        assert len(results) == 1
        assert results[0].severity == Severity.WARN
        assert results[0].fixer_id == "b4"

class TestB4Fixer:
    def test_injects_speed_caps_for_tpu(self) -> None:
        config = {...}
        B4FlexibleSpeedCapsFixer().apply(config, {}, Context(config=config))
        # 5 max_vol / (0.42 * 0.2) * 0.8 ≈ 47.6 mm/s
        assert config["outer_wall_speed"] == ["60", "47.6"] or similar
```

B5:
```python
class TestB5FlexibleSupport:
    def test_flexible_support_with_rigid_alt_emits_fix(self) -> None:
        config = {
            "filament_type": ["PLA", "TPU"],
            "filament_colour": ["#0", "#1"],
            "support_filament": "2",
            "support_interface_filament": "2",
        }
        results = B5FlexibleSupport().check(Context(config=config))
        assert len(results) == 1
        assert results[0].fixer_id == "b5"

    def test_flexible_support_no_rigid_warns_only(self) -> None:
        config = {
            "filament_type": ["TPU", "PEBA"],
            "filament_colour": ["#0", "#1"],
            "support_filament": "1",
            "support_interface_filament": "1",
        }
        results = B5FlexibleSupport().check(Context(config=config))
        assert len(results) == 1
        assert results[0].fixer_id is None  # warn-only

class TestB5Fixer:
    def test_reassigns_to_rigid(self) -> None:
        config = {...}  # same as above
        B5FlexibleSupportFixer().apply(config, {}, Context(config=config))
        assert config["support_filament"] == "1"
        assert config["support_interface_filament"] == "1"
```

**Step 2:** Run → FAIL.

**Step 3:** Implement.

**Step 4:** Run → PASS.

**Step 5:** Register in `u1kit/rules/__init__.py` and `u1kit/fixers/__init__.py`.

**Step 6:** Commit — `feat(b4,b5): flexible-filament speed caps and support swap`

---

### Task 9: C1 + C2 — bed-temperature conflict resolution

**Why:** Both C1 and C2 operate on parallel bed-temp arrays across the used-set. They share a `_min_over_used(config, field)` helper. C2 additionally handles the "missing `first_layer_bed_temperature`" gracefully (use `hot_plate_temp_initial_layer` fallback) and enforces the 65°C textured-PEI first-layer cap.

**Files:**
- Create: `u1kit/rules/c1_bed_temp_conflict.py`
- Create: `u1kit/fixers/c1_bed_temp_conflict.py`
- Create: `u1kit/rules/c2_first_layer_bed_temp.py`
- Create: `u1kit/fixers/c2_first_layer_bed_temp.py`
- Modify: `u1kit/rules/__init__.py`, `u1kit/fixers/__init__.py`
- Modify: `tests/test_rules.py`, `tests/test_fixers.py`

**C1 behavior:**
- Walks `hot_plate_temp`, `textured_plate_temp`, `cool_plate_temp`, `eng_plate_temp`, `supertack_plate_temp`, `textured_cool_plate_temp` over the used-set.
- If any field has ≥2 distinct values across used indices, emit FAIL.
- Fix: set every used index to `min(...)` for that field.

**C2 behavior:**
- Walks the `*_plate_temp_initial_layer` parallel arrays.
- If any has ≥2 distinct values among used indices, emit FAIL.
- Fix: set every used index to `min(...)`.
- Additionally: if any used first-layer value exceeds 65 and the active bed is textured-PEI (detected via `curr_bed_type == "textured_plate"` or presence of only textured-initial arrays), cap all used values at 65.

**Step 1 – 5:** Same TDD pattern.

**Commit:** `feat(c1,c2): bed-temperature conflict resolution across used filaments`

---

### Task 10: C3 + C4 — cooling time + fan range

**Why:** C3 picks the **max** `slow_down_layer_time` across used filaments (PEBA's 12s trumps PLA's 4s). C4 is info-only (spec:17 — "no single fix; surface per-filament ranges").

**Files:**
- Create: `u1kit/rules/c3_slow_down_layer_time.py` + fixer
- Create: `u1kit/rules/c4_fan_speed_range.py` (no fixer)
- Register in `__init__.py` files
- Test in `tests/test_rules.py` + `tests/test_fixers.py`

**C3 fixer:** set every used index's `slow_down_layer_time` to the max across used.
**C4:** emit an INFO Result with the per-filament fan ranges formatted in `diff_preview`; `fixer_id=None`.

**Commit:** `feat(c3,c4): cooling-time pick-max and fan-range surfacing`

---

### Task 11: D2 + D3 — Z-hop cap + mixed-alternation info

**Why:** Ground truth from `u1.3mf` shows Z-hop is a first-class parallel array (`z_hop`) and `mixed_filament_definitions` is a semicolon-CSV — both are much simpler than the spec hints suggested. Batch them since they're both Full Spectrum-adjacent.

**Files:**
- Create: `u1kit/rules/d2_z_hop_magnitude.py` + fixer
- Create: `u1kit/rules/d3_alternation_cost.py` (no fixer; info-only)
- Create: `u1kit/mixed_blends.py` — parser for `mixed_filament_definitions`
- Register
- Test

**D2 detail:**
- For each used filament, compute `max(z_hop[i], filament_z_hop[i])` (parsing nil/empty as 0).
- Flag FAIL (or WARN per spec — spec says warn) if that value ≥ `5 × layer_height`.
- Fix: set both `z_hop[i]` and `filament_z_hop[i]` to `max(1.5, 4 * layer_height)`.

**D3 detail:**
- Parse `mixed_filament_definitions` via `mixed_blends.py`. Each semicolon-separated entry is a CSV. The 5th field (index 4) is the ratio (observed as `50` for 1:1 on real file).
- If ≥1 entry has ratio == 50, emit INFO with "estimated N toolchanges per layer × M layers ≈ X toolchanges total" (use `layer_count = ceil(print_height / layer_height)` from config).
- No fix.

**Helper: `u1kit/mixed_blends.py`:**
```python
def parse_mixed_definitions(raw: str) -> list[MixedBlend]:
    """Parse 'a,b,c,d,50,...;...' into a list of MixedBlend dataclasses.
    Fields: filament_a, filament_b, ??? (0/1), ??? (0/1), ratio_percent, ???, ..."""
```
(Only the fields we actually use are named; the rest are stored as opaque strings so we don't lose fidelity on round-trip. Exact semantics of positions 2,3,5-11 are an open question — T2 already notes this as "parse what we understand, preserve the rest".)

**Step 1 – 5:** TDD.

**Commit:** `feat(d2,d3): z-hop cap via first-class field and 1:1 alternation info`

---

### Task 12: `u1kit/geometry.py` — 3D/3dmodel.model XML parser

**Why:** E1, E2, E3 all need to read object dimensions from `3D/3dmodel.model`. Split off as a prereq task so tests for the parser are isolated from tests for the rules that consume it.

**Files:**
- Create: `u1kit/geometry.py`
- Create: `tests/test_geometry.py`
- Modify: `tests/conftest.py` — add a fixture that injects a minimal `3D/3dmodel.model` XML into `make_3mf`

**API:**
```python
@dataclass
class ObjectBounds:
    id: str
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def thinnest_xy(self) -> float:
        return min(self.max_x - self.min_x, self.max_y - self.min_y)

def parse_model(xml_bytes: bytes) -> list[ObjectBounds]:
    """Parse a 3MF 3D/3dmodel.model XML and return bounding boxes per object.
    Uses xml.etree.ElementTree. Namespace: 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'."""

def total_plate_footprint(bounds: Iterable[ObjectBounds]) -> tuple[float, float]:
    """Return the (width, height) of the minimal bounding rectangle enclosing
    all objects projected to XY."""
```

**Notes:**
- The 3MF core XML has `<model>` → `<resources>` → `<object id="...">` → `<mesh>` → `<vertices>` → `<vertex x="..." y="..." z="..."/>`. Walk vertices to compute bounds.
- Large meshes (millions of verts) make this slow; accept that. The alternative is parsing `Metadata/model_settings.config` which may have precomputed bounds — check `u1.3mf`'s copy as a Phase 2 optimization if performance is a problem.

**Step 1: Failing test** using a tiny synthetic XML with 3 vertices.

**Commit:** `feat(geometry): 3dmodel.model XML parser for E-rules`

---

### Task 13: E1 — thin-feature / line-width warning

**Files:**
- Create: `u1kit/rules/e1_thin_feature.py` (no fixer — warn only per spec)
- Register
- Test

**Behavior:**
- Read `outer_wall_line_width` from config.
- Parse `3D/3dmodel.model` via `geometry.parse_model`.
- For each object: if `thinnest_xy / outer_wall_line_width < 3`, emit WARN Result with the object's ID and measurement.
- `fixer_id=None`.

**Commit:** `feat(e1): thin-feature warning based on object bounds`

---

### Task 14: E2 + E3 — layer-time info + prime tower brim

**Why:** Both consume geometry + `slow_down_layer_time` / prime-tower config. Shared math.

**Files:**
- Create: `u1kit/rules/e2_layer_time_clamp.py` (no fixer — info only)
- Create: `u1kit/rules/e3_prime_tower_brim.py` + optional fixer (warn, with auto-fix bumping `prime_tower_brim_width`)
- Register
- Test

**E2 behavior:**
- Compute `plate_footprint_area = width × depth` via `total_plate_footprint`.
- Compute `min_volumetric_speed = min(parse_float(filament_max_volumetric_speed[i]) for i in used)`.
- Layer time ≈ `(plate_footprint_area × layer_height) / min_volumetric_speed`.
- If layer time < `min(slow_down_layer_time[i] for i in used)`, emit INFO.

**E3 behavior:**
- If `total_plate_footprint` max dimension < 120mm AND `prime_tower_brim_width < 5`, emit WARN.
- Fix: set `prime_tower_brim_width` to `max(current, 5)`.

**Commit:** `feat(e2,e3): layer-time clamp info and prime tower brim bump`

---

### Task 15: F1 — Print Preprocessing dialog compatibility

**Files:**
- Create: `u1kit/rules/f1_lineage.py` (no fixer — info only per spec:27)
- Register
- Test

**Behavior:**
- For each used filament, check `filament_settings_id[i]`.
- Regex `r" @[A-Za-z0-9 ]+$"`:
  - If suffix missing or doesn't end with `@Snapmaker U1`: emit INFO. Message suggests "SD-card workflow or rebuild from Generic TPU base in Snapmaker Orca".
- No fix (spec: "no file-level fix possible").

**Commit:** `feat(f1): filament_settings_id lineage heuristic`

---

### Task 16: Ship remaining presets + Phase 2 exit verification

**Why:** Ships the four Phase 2 presets and runs the full exit-criteria check — every rule has at least one fixture test (checked during the batched rule tasks) and all 5 starter presets are runnable end-to-end.

**Files:**
- Create: `u1kit/presets/fs_uniform.yaml` (rules: `[D1]`)
- Create: `u1kit/presets/peba_safe.yaml` (rules: `[D1, D2, B4, B5, C3]`)
- Create: `u1kit/presets/plus_peba_multi.yaml` (rules: `[D1, D2, B4, B5, C3, C1, C2, C4]`)
- Create: `u1kit/presets/makerworld_import.yaml` (rules: `[A2, A3, B1, B2, B3, D1, C1, C2, B4]`)
- Modify: `tests/test_cli.py::TestPresets` — add assertions that all 5 preset names resolve
- Create: `tests/test_phase2_e2e.py` — one test per preset on an appropriate fixture
- Modify: `README.md` — update the rule table to include B4/B5/C1-C4/D2/D3/E1-E3/F1 and mark Phase 2 complete
- Modify: `DECISIONS.md` — lock in any open-question resolutions that became concrete during implementation
- Modify: `README.md` Status section to list Phase 2 coverage

**Steps:**
1. Create the four YAML files (near-trivial; mirror `bambu_to_u1.yaml` shape).
2. Add `TestPresets::test_all_starter_presets_list` — asserts `bambu-to-u1`, `fs-uniform`, `peba-safe`, `plus-peba-multi`, `makerworld-import` are all in the output.
3. Add `TestPhase2E2E::test_peba_safe_on_tpu_fixture` — synthesize a TPU-using .3mf, run `fix --preset peba-safe`, assert no remaining B4/B5/C3/D2 failures.
4. Add similar e2e tests for each preset.
5. Update README rule table and status.
6. Commit — `feat(phase2): ship remaining presets and verify exit criteria`

---

## Verification (Phase 2 exit criteria)

**All pass:**
- [ ] `pytest` — every rule has at least one test; every fixer has unit + idempotency tests
- [ ] `mypy --strict u1kit/` — clean
- [ ] `ruff check u1kit/ tests/` — clean
- [ ] `u1kit lint tests/fixtures/real/u1_native.3mf --json` — schema_version "1", 0 failures
- [ ] `u1kit presets list` — shows all 5 starter presets + any user-dir presets, tagged by source
- [ ] For each starter preset: `u1kit fix <appropriate-fixture> --preset <preset>` succeeds, output re-lints clean
- [ ] `u1.3mf` (at `tests/fixtures/real/u1_native.3mf`) round-trips byte-identical on non-config entries
- [ ] `DECISIONS.md` — every Phase 2 open question is either resolved or has a "deferred to Phase 3" note

**Sanity check:**
- [ ] Open one fixed file in Snapmaker Orca on a real machine if hardware available. (Not a blocker; spot-check only.)

---

## What's out of scope for Phase 2

- GUI (Phase 3)
- Sanitizer, batch mode, watch mode, packaging (Phase 4)
- prompt_toolkit rich TUI (Phase 3 GUI subsumes this)
- Plugin/entry-point rule discovery (Phase 4)
- Mesh-level thin-wall detection for E1 (bounding-box is a safe lower bound)
- Exact decode of `mixed_filament_definitions` positions 5-11 (parse ratio; preserve rest opaquely)
