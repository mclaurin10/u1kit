     │ u1kit Phase 1 Implementation Plan                                                         │
     │                                                                                           │
     │ ▎ For Claude: REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.                                                                                      │
     │                                                                                           │
     │ Goal: Build a Python CLI package that converts Bambu/Makerworld .3mf files into ones that print correctly on the Snapmaker U1.                                                              │
     │                                                                                           │
     │ Architecture: Three-layer pipeline — Rules (pure check functions), Fixers (config mutators), Pipeline (orchestrator with dry-run/auto/interactive modes). All file I/O goes through archive.py which preserves non-config ZIP entries byte-identical. Rules are checked in order; each may namfixer_id to invoke.                                           │
     │                                                                                           │
     │ Tech Stack: Python 3.11+, click, prompt_toolkit, pytest, ruff, mypy --strict, pyyaml      │
     │                                                                                           │
     │ ---                                                                                       │
     │ Context                                                                                   │
     │                                                                                           │
     │ User is building a slicer-file converter. Bambu-format .3mf files need printer profile rewriting, G-code macro replacement, filament mapping correction, and height-bound validation before they will load correctly in Snapmaker Orca. Phase 1 implements rules A1/A2/A3/B1/B2/B3/D1 plus thefull fixer pipeline and CLI. Real data files (printer reference  │
     │ JSON, toolchange G-code) are stubs — placeholders with clear TODO markers.                │
     │                                                                                           │
     │ ---                                                                                       │
     │ File Tree                                                                                 │
     │                                                                                           │
     │ u1kit/                                                                                    │
     │   __init__.py                                                                             │
     │   archive.py                                                                              │
     │   config.py                                                                               │
     │   rules/                                                                                  │
     │     __init__.py                                                                           │
     │     base.py                                                                               │
     │     a1_source_slicer.py                                                                   │
     │     a2_printer_profile.py                                                                 │
     │     a3_bambu_macros.py                                                                    │
     │     b2_filament_mapping.py                                                                │
     │     b3_bbl_fields.py                                                                      │
     │     d1_mixed_height_bounds.py                                                             │
     │   fixers/                                                                                 │
     │     __init__.py                                                                           │
     │     base.py                                                                               │
     │     fix_printer_profile.py                                                                │
     │     fix_toolchange_gcode.py                                                               │
     │     fix_filament_mapping.py                                                               │
     │     fix_bbl_fields.py                                                                     │
     │     fix_mixed_height_bounds.py                                                            │
     │   presets/                                                                                │
     │     bambu_to_u1.yaml                                                                      │
     │   report.py                                                                               │
     │   data/                                                                                   │
     │     u1_printer_reference.json                                                             │
     │     u1_toolchange.gcode                                                                   │
     │   cli.py                                                                                  │
     │ tests/                                                                                    │
     │   conftest.py                                                                             │
     │   fixtures/                                                                               │
     │   test_archive_roundtrip.py                                                               │
     │   test_rules_a1.py                                                                        │
     │   test_rules_a2.py                                                                        │
     │   test_rules_a3.py                                                                        │
     │   test_rules_b2.py                                                                        │
     │   test_rules_b3.py                                                                        │
     │   test_rules_d1.py                                                                        │
     │   test_fixers.py                                                                          │
     │   test_cli.py                                                                             │
     │ pyproject.toml                                                                            │
     │ DECISIONS.md                                                                              │
     │ README.md                                                                                 │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 1: Project Scaffold                                                                  │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: pyproject.toml                                                                  │
     │ - Create: u1kit/__init__.py and all sub-package __init__.py stubs                         │
     │ - Create: DECISIONS.md                                                                    │
     │ - Create: README.md (exit criteria section only)                                          │
     │                                                                                           │
     │ Step 1: Create pyproject.toml                                                             │
     │                                                                                           │
     │ [build-system]                                                                            │
     │ requires = ["hatchling"]                                                                  │
     │ build-backend = "hatchling.build"                                                         │
     │                                                                                           │
     │ [project]                                                                                 │
     │ name = "u1kit"                                                                            │
     │ version = "0.1.0"                                                                         │
     │ requires-python = ">=3.11"                                                                │
     │ dependencies = [                                                                          │
     │     "click>=8.1",                                                                         │
     │     "prompt_toolkit>=3.0",                                                                │
     │     "pyyaml>=6.0",                                                                        │
     │ ]                                                                                         │
     │                                                                                           │
     │ [project.scripts]                                                                         │
     │ u1kit = "u1kit.cli:main"                                                                  │
     │                                                                                           │
     │ [tool.ruff]                                                                               │
     │ target-version = "py311"                                                                  │
     │ lint.select = ["E", "F", "I", "UP", "B", "SIM"]                                           │
     │                                                                                           │
     │ [tool.mypy]                                                                               │
     │ strict = true                                                                             │
     │ python_version = "3.11"                                                                   │
     │                                                                                           │
     │ [tool.pytest.ini_options]                                                                 │
     │ testpaths = ["tests"]                                                                     │
     │                                                                                           │
     │ Step 2: Create all __init__.py stubs                                                      │
     │                                                                                           │
     │ Each sub-package needs an __init__.py. Keep them empty except u1kit/__init__.py:          │
     │                                                                                           │
     │ # u1kit/__init__.py                                                                       │
     │ """u1kit — Bambu .3mf → Snapmaker U1 converter."""                                        │
     │ __version__ = "0.1.0"                                                                     │
     │                                                                                           │
     │ Step 3: Create DECISIONS.md                                                               │
     │                                                                                           │
     │ # DECISIONS.md                                                                            │
     │                                                                                           │
     │ ## Open Questions                                                                         │
     │                                                                                           │
     │ ### OQ-1: Archive fidelity (ZIP compression/ordering/timestamps)                          │
     │ **Decision:** Preserve original ZipInfo (compress_type + date_time) for all entries.      │
     │ For entries we rewrite (config JSON), keep original date_time but switch compress_type    │
     │ to ZIP_DEFLATED. Entry ordering matches original infolist() order.                        │
     │ **Status:** Flagged for spike with real Snapmaker Orca files.                             │
     │                                                                                           │
     │ ### OQ-2: A3 G-code template                                                              │
     │ **Decision:** Placeholder file `u1kit/data/u1_toolchange.gcode` with TODO header.         │
     │ Code always loads from disk — swapping is a one-file change with no code edits.           │
     │ **Status:** Awaiting real export from Snapmaker Orca.                                     │
     │                                                                                           │
     │ ### OQ-3: B1 interactive merge (filament count > 4)                                       │
     │ **Decision:** Phase 1 is report-only (fail severity, no fixer_id).                        │
     │ Deferred to Phase 2 per spec.                                                             │
     │                                                                                           │
     │ ## Implementation Choices                                                                 │
     │                                                                                           │
     │ ### IC-1: CLI framework                                                                   │
     │ **Choice:** click (over argparse). More ergonomic for nested commands, easier testing     │
     │ with CliRunner, good --help generation.                                                   │
     │                                                                                           │
     │ ### IC-2: u1_printer_reference.json placeholder                                           │
     │ All keys present with clearly marked TODO values. See `u1kit/data/u1_printer_reference.json`.                                                                                               │
     │                                                                                           │
     │ Step 4: Install in dev mode and verify imports                                            │
     │                                                                                           │
     │ pip install -e ".[dev]"                                                                   │
     │ python -c "import u1kit; print(u1kit.__version__)"                                        │
     │                                                                                           │
     │ Expected: 0.1.0                                                                           │
     │                                                                                           │
     │ Step 5: Commit                                                                            │
     │                                                                                           │
     │ git init                                                                                  │
     │ git add pyproject.toml u1kit/ DECISIONS.md README.md                                      │
     │ git commit -m "chore: scaffold u1kit package structure"                                   │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 2: archive.py — ZIP round-trip                                                       │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/archive.py                                                                │
     │ - Create: tests/test_archive_roundtrip.py                                                 │
     │ - Create: tests/conftest.py (shared fixture helpers)                                      │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/conftest.py                                                                       │
     │ import io, json, zipfile                                                                  │
     │ from pathlib import Path                                                                  │
     │ import pytest                                                                             │
     │                                                                                           │
     │ MINIMAL_PROJECT_SETTINGS = {                                                              │
     │     "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",                              │
     │     "printer_model": "BambuLab X1 Carbon",                                                │
     │     "layer_height": "0.2",                                                                │
     │     "filament_map": [1, 2],                                                               │
     │ }                                                                                         │
     │                                                                                           │
     │ def make_3mf(                                                                             │
     │     project_settings: dict,                                                               │
     │     filament_settings: list[dict] | None = None,                                          │
     │     extra_entries: dict[str, bytes] | None = None,                                        │
     │ ) -> bytes:                                                                               │
     │     """Build a minimal .3mf ZIP in memory."""                                             │
     │     buf = io.BytesIO()                                                                    │
     │     with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:               │
     │         zf.writestr(                                                                      │
     │             "Metadata/project_settings.config",                                           │
     │             json.dumps(project_settings),                                                 │
     │         )                                                                                 │
     │         for i, fs in enumerate(filament_settings or []):                                  │
     │             zf.writestr(f"Metadata/filament_settings_{i}.config", json.dumps(fs))         │
     │         for name, data in (extra_entries or {}).items():                                  │
     │             zf.writestr(name, data, compress_type=zipfile.ZIP_STORED)                     │
     │     return buf.getvalue()                                                                 │
     │                                                                                           │
     │ # tests/test_archive_roundtrip.py                                                         │
     │ import io, json, zipfile                                                                  │
     │ from pathlib import Path                                                                  │
     │ import pytest                                                                             │
     │ from u1kit.archive import Archive3mf                                                      │
     │ from tests.conftest import make_3mf, MINIMAL_PROJECT_SETTINGS                             │
     │                                                                                           │
     │ FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # fake PNG bytes                          │
     │ FAKE_MODEL = b"<model/>"  # fake 3D model blob                                            │
     │                                                                                           │
     │ def test_read_project_settings():                                                         │
     │     data = make_3mf(MINIMAL_PROJECT_SETTINGS)                                             │
     │     arch = Archive3mf.from_bytes(data)                                                    │
     │     cfg = arch.get_project_settings()                                                     │
     │     assert cfg["printer_model"] == "BambuLab X1 Carbon"                                   │
     │                                                                                           │
     │ def test_non_config_entries_byte_identical():                                             │
     │     """Non-config entries must survive round-trip unchanged."""                           │
     │     data = make_3mf(                                                                      │
     │         MINIMAL_PROJECT_SETTINGS,                                                         │
     │         extra_entries={                                                                   │
     │             "Metadata/thumbnail.png": FAKE_PNG,                                           │
     │             "3D/3dmodel.model": FAKE_MODEL,                                               │
     │         },                                                                                │
     │     )                                                                                     │
     │     arch = Archive3mf.from_bytes(data)                                                    │
     │     out = arch.to_bytes()                                                                 │
     │                                                                                           │
     │     with zipfile.ZipFile(io.BytesIO(out)) as zf:                                          │
     │         assert zf.read("Metadata/thumbnail.png") == FAKE_PNG                              │
     │         assert zf.read("3D/3dmodel.model") == FAKE_MODEL                                  │
     │                                                                                           │
     │ def test_config_rewrite_preserves_others():                                               │
     │     """Rewriting config must not corrupt other entries."""                                │
     │     data = make_3mf(                                                                      │
     │         MINIMAL_PROJECT_SETTINGS,                                                         │
     │         extra_entries={"Metadata/thumbnail.png": FAKE_PNG},                               │
     │     )                                                                                     │
     │     arch = Archive3mf.from_bytes(data)                                                    │
     │     new_cfg = {**arch.get_project_settings(), "printer_model": "Snapmaker U1"}            │
     │     arch.set_project_settings(new_cfg)                                                    │
     │     out = arch.to_bytes()                                                                 │
     │                                                                                           │
     │     with zipfile.ZipFile(io.BytesIO(out)) as zf:                                          │
     │         assert json.loads(zf.read("Metadata/project_settings.config"))["printer_model"] =="Snapmaker U1"                                                                                    │
     │         assert zf.read("Metadata/thumbnail.png") == FAKE_PNG                              │
     │                                                                                           │
     │ def test_filament_configs_roundtrip():                                                    │
     │     data = make_3mf(                                                                      │
     │         MINIMAL_PROJECT_SETTINGS,                                                         │
     │         filament_settings=[{"filament_type": "PLA"}, {"filament_type": "PETG"}],          │
     │     )                                                                                     │
     │     arch = Archive3mf.from_bytes(data)                                                    │
     │     filaments = arch.get_filament_settings()                                              │
     │     assert len(filaments) == 2                                                            │
     │     assert filaments[0]["filament_type"] == "PLA"                                         │
     │                                                                                           │
     │ Step 2: Run to confirm failure                                                            │
     │                                                                                           │
     │ pytest tests/test_archive_roundtrip.py -v                                                 │
     │                                                                                           │
     │ Expected: ImportError: cannot import name 'Archive3mf'                                    │
     │                                                                                           │
     │ Step 3: Implement archive.py                                                              │
     │                                                                                           │
     │ # u1kit/archive.py                                                                        │
     │ """ZIP archive I/O for .3mf files with byte-identical passthrough."""                     │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ import io                                                                                 │
     │ import json                                                                               │
     │ import zipfile                                                                            │
     │ from dataclasses import dataclass, field                                                  │
     │ from pathlib import Path                                                                  │
     │ from typing import Any                                                                    │
     │                                                                                           │
     │ PROJECT_CONFIG_PATH = "Metadata/project_settings.config"                                  │
     │ FILAMENT_CONFIG_GLOB = "Metadata/filament_settings"  # prefix match                       │
     │                                                                                           │
     │ @dataclass                                                                                │
     │ class Archive3mf:                                                                         │
     │     _entries: dict[str, bytes] = field(default_factory=dict)                              │
     │     _infos: dict[str, zipfile.ZipInfo] = field(default_factory=dict)                      │
     │     _order: list[str] = field(default_factory=list)  # preserve entry order               │
     │     _modified: set[str] = field(default_factory=set)                                      │
     │                                                                                           │
     │     @classmethod                                                                          │
     │     def from_path(cls, path: Path) -> "Archive3mf":                                       │
     │         return cls.from_bytes(path.read_bytes())                                          │
     │                                                                                           │
     │     @classmethod                                                                          │
     │     def from_bytes(cls, data: bytes) -> "Archive3mf":                                     │
     │         obj = cls()                                                                       │
     │         with zipfile.ZipFile(io.BytesIO(data), "r") as zf:                                │
     │             for info in zf.infolist():                                                    │
     │                 obj._entries[info.filename] = zf.read(info.filename)                      │
     │                 obj._infos[info.filename] = info                                          │
     │                 obj._order.append(info.filename)                                          │
     │         return obj                                                                        │
     │                                                                                           │
     │     def get_project_settings(self) -> dict[str, Any]:                                     │
     │         return json.loads(self._entries[PROJECT_CONFIG_PATH])                             │
     │                                                                                           │
     │     def set_project_settings(self, cfg: dict[str, Any]) -> None:                          │
     │         self._entries[PROJECT_CONFIG_PATH] = json.dumps(cfg, indent=2).encode()           │
     │         self._modified.add(PROJECT_CONFIG_PATH)                                           │
     │                                                                                           │
     │     def get_filament_settings(self) -> list[dict[str, Any]]:                              │
     │         keys = sorted(                                                                    │
     │             k for k in self._order                                                        │
     │             if k.startswith(FILAMENT_CONFIG_GLOB) and k.endswith(".config")               │
     │         )                                                                                 │
     │         return [json.loads(self._entries[k]) for k in keys]                               │
     │                                                                                           │
     │     def get_filament_setting_keys(self) -> list[str]:                                     │
     │         return sorted(                                                                    │
     │             k for k in self._order                                                        │
     │             if k.startswith(FILAMENT_CONFIG_GLOB) and k.endswith(".config")               │
     │         )                                                                                 │
     │                                                                                           │
     │     def set_filament_setting(self, key: str, cfg: dict[str, Any]) -> None:                │
     │         self._entries[key] = json.dumps(cfg, indent=2).encode()                           │
     │         self._modified.add(key)                                                           │
     │                                                                                           │
     │     def to_bytes(self) -> bytes:                                                          │
     │         buf = io.BytesIO()                                                                │
     │         with zipfile.ZipFile(buf, "w") as zf:                                             │
     │             for name in self._order:                                                      │
     │                 original_info = self._infos[name]                                         │
     │                 if name in self._modified:                                                │
     │                     # rewritten: keep original mtime, switch to DEFLATED                  │
     │                     new_info = zipfile.ZipInfo(name, date_time=original_info.date_time)   │
     │                     new_info.compress_type = zipfile.ZIP_DEFLATED                         │
     │                     zf.writestr(new_info, self._entries[name])                            │
     │                 else:                                                                     │
     │                     # passthrough: preserve compression type and mtime                    │
     │                     new_info = zipfile.ZipInfo(name, date_time=original_info.date_time)   │
     │                     new_info.compress_type = original_info.compress_type                  │
     │                     zf.writestr(new_info, self._entries[name])                            │
     │         return buf.getvalue()                                                             │
     │                                                                                           │
     │     def to_path(self, path: Path) -> None:                                                │
     │         path.write_bytes(self.to_bytes())                                                 │
     │                                                                                           │
     │ Step 4: Run tests                                                                         │
     │                                                                                           │
     │ pytest tests/test_archive_roundtrip.py -v                                                 │
     │                                                                                           │
     │ Expected: all 4 PASS                                                                      │
     │                                                                                           │
     │ Step 5: Commit                                                                            │
     │                                                                                           │
     │ git add u1kit/archive.py tests/test_archive_roundtrip.py tests/conftest.py                │
     │ git commit -m "feat: archive.py with byte-identical ZIP round-trip"                       │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 3: config.py — parse/emit helpers                                                    │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/config.py                                                                 │
     │                                                                                           │
     │ This module is thin — it's a convenience layer over archive.py. No separate test file; tested via rule tests.                                                                               │
     │                                                                                           │
     │ # u1kit/config.py                                                                         │
     │ """Convenience wrappers for reading/writing project config from an Archive3mf."""         │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from dataclasses import dataclass, field                                                  │
     │ from typing import Any                                                                    │
     │                                                                                           │
     │ from u1kit.archive import Archive3mf                                                      │
     │                                                                                           │
     │                                                                                           │
     │ @dataclass                                                                                │
     │ class ProjectConfig:                                                                      │
     │     """Mutable view of project_settings.config + filament blobs."""                       │
     │     settings: dict[str, Any]                                                              │
     │     filament_keys: list[str]                                                              │
     │     filament_settings: list[dict[str, Any]]                                               │
     │                                                                                           │
     │     @classmethod                                                                          │
     │     def from_archive(cls, arch: Archive3mf) -> "ProjectConfig":                           │
     │         return cls(                                                                       │
     │             settings=arch.get_project_settings(),                                         │
     │             filament_keys=arch.get_filament_setting_keys(),                               │
     │             filament_settings=arch.get_filament_settings(),                               │
     │         )                                                                                 │
     │                                                                                           │
     │     def flush(self, arch: Archive3mf) -> None:                                            │
     │         """Write mutated config back into the archive."""                                 │
     │         arch.set_project_settings(self.settings)                                          │
     │         for key, cfg in zip(self.filament_keys, self.filament_settings):                  │
     │             arch.set_filament_setting(key, cfg)                                           │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/config.py                                                                   │
     │ git commit -m "feat: config.py ProjectConfig view over archive"                           │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 4: Rule base + registry                                                              │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/base.py                                                             │
     │ - Create: u1kit/rules/__init__.py                                                         │
     │                                                                                           │
     │ Step 1: Write base.py                                                                     │
     │                                                                                           │
     │ # u1kit/rules/base.py                                                                     │
     │ """Rule protocol, Result, Severity — the public API contract for all rules."""            │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from dataclasses import dataclass, field                                                  │
     │ from enum import Enum                                                                     │
     │ from typing import Any, Protocol                                                          │
     │                                                                                           │
     │                                                                                           │
     │ class Severity(str, Enum):                                                                │
     │     fail = "fail"                                                                         │
     │     warn = "warn"                                                                         │
     │     info = "info"                                                                         │
     │                                                                                           │
     │                                                                                           │
     │ @dataclass                                                                                │
     │ class Result:                                                                             │
     │     rule_id: str                                                                          │
     │     severity: Severity                                                                    │
     │     message: str                                                                          │
     │     fixer_id: str | None = None                                                           │
     │     diff_preview: str | None = None                                                       │
     │                                                                                           │
     │                                                                                           │
     │ @dataclass                                                                                │
     │ class RuleContext:                                                                        │
     │     settings: dict[str, Any]                                                              │
     │     filament_keys: list[str]                                                              │
     │     filament_settings: list[dict[str, Any]]                                               │
     │     source_slicer: str | None = None   # populated by A1 for downstream rules             │
     │     uniform_height: float = 0.2        # CLI-configurable, used by D1                     │
     │                                                                                           │
     │                                                                                           │
     │ class Rule(Protocol):                                                                     │
     │     id: str                                                                               │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         ...                                                                               │
     │                                                                                           │
     │ Step 2: Write rules/init.py with registry                                                 │
     │                                                                                           │
     │ # u1kit/rules/__init__.py                                                                 │
     │ """Rule registry — maps rule_id str → Rule instance."""                                   │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from typing import TYPE_CHECKING                                                          │
     │                                                                                           │
     │ if TYPE_CHECKING:                                                                         │
     │     from u1kit.rules.base import Rule                                                     │
     │                                                                                           │
     │ _REGISTRY: dict[str, "Rule"] = {}                                                         │
     │                                                                                           │
     │                                                                                           │
     │ def register(rule: "Rule") -> "Rule":                                                     │
     │     _REGISTRY[rule.id] = rule                                                             │
     │     return rule                                                                           │
     │                                                                                           │
     │                                                                                           │
     │ def get(rule_id: str) -> "Rule":                                                          │
     │     return _REGISTRY[rule_id]                                                             │
     │                                                                                           │
     │                                                                                           │
     │ def all_rules() -> list["Rule"]:                                                          │
     │     return list(_REGISTRY.values())                                                       │
     │                                                                                           │
     │                                                                                           │
     │ # Import rules to trigger registration (order = run order)                                │
     │ from u1kit.rules.a1_source_slicer import rule as _a1  # noqa: E402, F401                  │
     │ from u1kit.rules.a2_printer_profile import rule as _a2  # noqa: E402, F401                │
     │ from u1kit.rules.a3_bambu_macros import rule as _a3  # noqa: E402, F401                   │
     │ from u1kit.rules.b2_filament_mapping import rule as _b2  # noqa: E402, F401               │
     │ from u1kit.rules.b3_bbl_fields import rule as _b3  # noqa: E402, F401                     │
     │ from u1kit.rules.d1_mixed_height_bounds import rule as _d1  # noqa: E402, F401            │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/rules/base.py u1kit/rules/__init__.py                                       │
     │ git commit -m "feat: rule base types and registry"                                        │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 5: Data stubs                                                                        │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/data/u1_printer_reference.json                                            │
     │ - Create: u1kit/data/u1_toolchange.gcode                                                  │
     │                                                                                           │
     │ Step 1: Create u1_printer_reference.json                                                  │
     │                                                                                           │
     │ {                                                                                         │
     │   "_TODO": "Replace all placeholder values with real Snapmaker U1 Orca export values",    │
     │   "printer_settings_id": "Snapmaker U1 0.4 nozzle",                                       │
     │   "printer_model": "SnapmakerU1",                                                         │
     │   "printable_area": [                                                                     │
     │     [0, 0], [320, 0], [320, 320], [0, 320]                                                │
     │   ],                                                                                      │
     │   "printable_height": "320",                                                              │
     │   "machine_max_acceleration_e": ["5000", "5000"],                                         │
     │   "machine_max_acceleration_extruding": ["5000", "5000"],                                 │
     │   "machine_max_acceleration_retracting": ["5000", "5000"],                                │
     │   "machine_max_acceleration_travel": ["5000", "5000"],                                    │
     │   "machine_max_acceleration_x": ["5000", "5000"],                                         │
     │   "machine_max_acceleration_y": ["5000", "5000"],                                         │
     │   "machine_max_acceleration_z": ["400", "400"],                                           │
     │   "machine_max_jerk_e": ["2.5", "2.5"],                                                   │
     │   "machine_max_jerk_x": ["10", "10"],                                                     │
     │   "machine_max_jerk_y": ["10", "10"],                                                     │
     │   "machine_max_jerk_z": ["0.4", "0.4"],                                                   │
     │   "machine_max_speed_e": ["25", "25"],                                                    │
     │   "machine_max_speed_x": ["500", "500"],                                                  │
     │   "machine_max_speed_y": ["500", "500"],                                                  │
     │   "machine_max_speed_z": ["20", "20"]                                                     │
     │ }                                                                                         │
     │                                                                                           │
     │ Step 2: Create u1_toolchange.gcode                                                        │
     │                                                                                           │
     │ ; TODO: Replace with known-good Snapmaker Orca toolchange export                          │
     │ ; This is a placeholder. The actual toolchange G-code must be obtained                    │
     │ ; from a real Snapmaker U1 Orca Slicer export.                                            │
     │ T{next_extruder}                                                                          │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/data/                                                                       │
     │ git commit -m "chore: stub data files for U1 printer reference and toolchange gcode"      │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 6: Rule A1 — Source slicer detection                                                 │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/a1_source_slicer.py                                                 │
     │ - Create: tests/test_rules_a1.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_a1.py                                                                  │
     │ import pytest                                                                             │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.a1_source_slicer import rule                                             │
     │                                                                                           │
     │ def make_ctx(settings: dict) -> RuleContext:                                              │
     │     return RuleContext(settings=settings, filament_keys=[], filament_settings=[])         │
     │                                                                                           │
     │ def test_detects_bambu():                                                                 │
     │     ctx = make_ctx({"printer_settings_id": "Bambu Lab X1C 0.4 nozzle", "printer_model": "BambuLab X1C"})                                                                                    │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert results[0].severity == Severity.info                                           │
     │     assert "bambu" in results[0].message.lower()                                          │
     │                                                                                           │
     │ def test_detects_full_spectrum():                                                         │
     │     ctx = make_ctx({                                                                      │
     │         "printer_settings_id": "SomeOtherSlicer",                                         │
     │         "printer_model": "SomePrinter",                                                   │
     │         "mixed_filament_height_lower_bound": "0.04",                                      │
     │     })                                                                                    │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert "full spectrum" in results[0].message.lower()                                  │
     │                                                                                           │
     │ def test_unknown_source():                                                                │
     │     ctx = make_ctx({"printer_settings_id": "Generic FDM", "printer_model": "MyCoolPrinter"})                                                                                                │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert "unknown" in results[0].message.lower()                                        │
     │                                                                                           │
     │ def test_sets_source_slicer_on_context():                                                 │
     │     """A1 must mutate ctx.source_slicer so downstream rules can gate."""                  │
     │     ctx = make_ctx({"printer_settings_id": "Bambu Lab P1S 0.4 nozzle", "printer_model": "BambuLab P1S"})                                                                                    │
     │     rule.check(ctx)                                                                       │
     │     assert ctx.source_slicer == "bambu"                                                   │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/a1_source_slicer.py                                                         │
     │ """A1 — detect source slicer (info, no fixer)."""                                         │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ _BAMBU_HINTS = ("bambu", "bbl", "bblslicer")                                              │
     │ _FULL_SPECTRUM_KEY = "mixed_filament_height_lower_bound"                                  │
     │                                                                                           │
     │                                                                                           │
     │ class A1Rule:                                                                             │
     │     id = "A1"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         settings_id = str(ctx.settings.get("printer_settings_id", "")).lower()            │
     │         model = str(ctx.settings.get("printer_model", "")).lower()                        │
     │         has_fs_keys = _FULL_SPECTRUM_KEY in ctx.settings                                  │
     │                                                                                           │
     │         if any(h in settings_id or h in model for h in _BAMBU_HINTS):                     │
     │             ctx.source_slicer = "bambu"                                                   │
     │             return [Result(                                                               │
     │                 rule_id=self.id,                                                          │
     │                 severity=Severity.info,                                                   │
     │                 message=f"Source slicer detected: Bambu (printer_settings_id={ctx.settings.get('printer_settings_id')!r})",                                                                 │
     │             )]                                                                            │
     │                                                                                           │
     │         if has_fs_keys:                                                                   │
     │             ctx.source_slicer = "full_spectrum"                                           │
     │             return [Result(                                                               │
     │                 rule_id=self.id,                                                          │
     │                 severity=Severity.info,                                                   │
     │                 message="Source slicer detected: Full Spectrum (mixed_filament_height_* keys present)",                                                                                     │
     │             )]                                                                            │
     │                                                                                           │
     │         ctx.source_slicer = "unknown"                                                     │
     │         return [Result(                                                                   │
     │             rule_id=self.id,                                                              │
     │             severity=Severity.info,                                                       │
     │             message=f"Source slicer unknown — proceeding with generic conversion (printer_model={ctx.settings.get('printer_model')!r})",                                                    │
     │         )]                                                                                │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(A1Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests                                                                         │
     │                                                                                           │
     │ pytest tests/test_rules_a1.py -v                                                          │
     │                                                                                           │
     │ Expected: 4 PASS                                                                          │
     │                                                                                           │
     │ Step 4: Commit                                                                            │
     │                                                                                           │
     │ git add u1kit/rules/a1_source_slicer.py tests/test_rules_a1.py                            │
     │ git commit -m "feat(rule): A1 source slicer detection"                                    │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 7: Rule A2 — Printer profile                                                         │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/a2_printer_profile.py                                               │
     │ - Create: tests/test_rules_a2.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_a2.py                                                                  │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.a2_printer_profile import rule                                           │
     │                                                                                           │
     │ def make_ctx(settings: dict) -> RuleContext:                                              │
     │     return RuleContext(settings=settings, filament_keys=[], filament_settings=[])         │
     │                                                                                           │
     │ def test_fails_on_bambu_profile():                                                        │
     │     ctx = make_ctx({"printer_settings_id": "Bambu Lab X1C 0.4", "printer_model": "BambuLabX1C"})                                                                                            │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     r = results[0]                                                                        │
     │     assert r.severity == Severity.fail                                                    │
     │     assert r.fixer_id == "fix_printer_profile"                                            │
     │     assert "A2" in r.rule_id                                                              │
     │                                                                                           │
     │ def test_passes_on_u1_profile():                                                          │
     │     # Use the exact printer_settings_id from u1_printer_reference.json                    │
     │     ctx = make_ctx({"printer_settings_id": "Snapmaker U1 0.4 nozzle", "printer_model": "SnapmakerU1"})                                                                                      │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ def test_diff_preview_shows_before_after():                                               │
     │     ctx = make_ctx({"printer_settings_id": "Bambu Lab X1C 0.4", "printer_model": "BambuLabX1C"})                                                                                            │
     │     results = rule.check(ctx)                                                             │
     │     assert results[0].diff_preview is not None                                            │
     │     assert "Bambu" in results[0].diff_preview                                             │
     │     assert "Snapmaker" in results[0].diff_preview                                         │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/a2_printer_profile.py                                                       │
     │ """A2 — printer profile mismatch (fail, fixer=fix_printer_profile)."""                    │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ import json                                                                               │
     │ from importlib.resources import files                                                     │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ def _load_reference() -> dict:                                                            │
     │     data = files("u1kit.data").joinpath("u1_printer_reference.json").read_text()          │
     │     return json.loads(data)                                                               │
     │                                                                                           │
     │ _REF: dict | None = None                                                                  │
     │                                                                                           │
     │ def _ref() -> dict:                                                                       │
     │     global _REF                                                                           │
     │     if _REF is None:                                                                      │
     │         _REF = _load_reference()                                                          │
     │     return _REF                                                                           │
     │                                                                                           │
     │                                                                                           │
     │ class A2Rule:                                                                             │
     │     id = "A2"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         ref = _ref()                                                                      │
     │         current_id = ctx.settings.get("printer_settings_id", "")                          │
     │         current_model = ctx.settings.get("printer_model", "")                             │
     │                                                                                           │
     │         if current_id == ref["printer_settings_id"] and current_model == ref["printer_model"]:                                                                                              │
     │             return []                                                                     │
     │                                                                                           │
     │         diff = (                                                                          │
     │             f"printer_settings_id: {current_id!r} → {ref['printer_settings_id']!r}\n"     │
     │             f"printer_model: {current_model!r} → {ref['printer_model']!r}"                │
     │         )                                                                                 │
     │         return [Result(                                                                   │
     │             rule_id=self.id,                                                              │
     │             severity=Severity.fail,                                                       │
     │             message=f"Printer profile is not U1 (found {current_id!r}). Run fixer to rewrite.",                                                                                             │
     │             fixer_id="fix_printer_profile",                                               │
     │             diff_preview=diff,                                                            │
     │         )]                                                                                │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(A2Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests, commit                                                                 │
     │                                                                                           │
     │ pytest tests/test_rules_a2.py -v                                                          │
     │ git add u1kit/rules/a2_printer_profile.py tests/test_rules_a2.py                          │
     │ git commit -m "feat(rule): A2 printer profile mismatch"                                   │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 8: Rule A3 — Bambu macros in G-code                                                  │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/a3_bambu_macros.py                                                  │
     │ - Create: tests/test_rules_a3.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_a3.py                                                                  │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.a3_bambu_macros import rule                                              │
     │                                                                                           │
     │ def make_ctx(start="", end="", change="", layer="") -> RuleContext:                       │
     │     return RuleContext(                                                                   │
     │         settings={                                                                        │
     │             "machine_start_gcode": start,                                                 │
     │             "machine_end_gcode": end,                                                     │
     │             "change_filament_gcode": change,                                              │
     │             "layer_change_gcode": layer,                                                  │
     │         },                                                                                │
     │         filament_keys=[],                                                                 │
     │         filament_settings=[],                                                             │
     │     )                                                                                     │
     │                                                                                           │
     │ def test_detects_M620():                                                                  │
     │     ctx = make_ctx(change="M620 S1A\nT1\nM621 S1A")                                       │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert results[0].severity == Severity.fail                                           │
     │     assert results[0].fixer_id == "fix_toolchange_gcode"                                  │
     │                                                                                           │
     │ def test_detects_M621():                                                                  │
     │     ctx = make_ctx(end="M621 S0A")                                                        │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │                                                                                           │
     │ def test_detects_M623():                                                                  │
     │     ctx = make_ctx(start="M623")                                                          │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │                                                                                           │
     │ def test_detects_AMS_syntax():                                                            │
     │     ctx = make_ctx(change="; AMS filament change\nM620 S{next_extruder}A")                │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │                                                                                           │
     │ def test_clean_gcode_passes():                                                            │
     │     ctx = make_ctx(                                                                       │
     │         start="; Start\nG28\nG1 Z5",                                                      │
     │         end="; End\nM104 S0",                                                             │
     │         change="T{next_extruder}",                                                        │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/a3_bambu_macros.py                                                          │
     │ """A3 — Bambu AMS/toolchange macros in G-code fields (fail, fixer=fix_toolchange_gcode).""│
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ import re                                                                                 │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ _GCODE_FIELDS = (                                                                         │
     │     "machine_start_gcode",                                                                │
     │     "machine_end_gcode",                                                                  │
     │     "change_filament_gcode",                                                              │
     │     "layer_change_gcode",                                                                 │
     │ )                                                                                         │
     │                                                                                           │
     │ # Patterns that indicate Bambu AMS / toolchange macro syntax                              │
     │ _BAMBU_PATTERNS: list[re.Pattern[str]] = [                                                │
     │     re.compile(r"\bM620\b"),                                                              │
     │     re.compile(r"\bM621\b"),                                                              │
     │     re.compile(r"\bM623\b"),                                                              │
     │     re.compile(r"\bAMS\b", re.IGNORECASE),                                                │
     │ ]                                                                                         │
     │                                                                                           │
     │                                                                                           │
     │ class A3Rule:                                                                             │
     │     id = "A3"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         hits: list[str] = []                                                              │
     │         for field in _GCODE_FIELDS:                                                       │
     │             gcode = ctx.settings.get(field, "")                                           │
     │             for pat in _BAMBU_PATTERNS:                                                   │
     │                 if pat.search(gcode):                                                     │
     │                     hits.append(f"{field}: matches {pat.pattern!r}")                      │
     │                     break  # one hit per field is enough                                  │
     │                                                                                           │
     │         if not hits:                                                                      │
     │             return []                                                                     │
     │                                                                                           │
     │         return [Result(                                                                   │
     │             rule_id=self.id,                                                              │
     │             severity=Severity.fail,                                                       │
     │             message=f"Bambu AMS/toolchange macros found in G-code fields: {'; '.join(hits)}",                                                                                               │
     │             fixer_id="fix_toolchange_gcode",                                              │
     │             diff_preview=f"Affected fields: {', '.join(f.split(':')[0] for f in hits)}",  │
     │         )]                                                                                │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(A3Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests, commit                                                                 │
     │                                                                                           │
     │ pytest tests/test_rules_a3.py -v                                                          │
     │ git add u1kit/rules/a3_bambu_macros.py tests/test_rules_a3.py                             │
     │ git commit -m "feat(rule): A3 Bambu AMS macro detection"                                  │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 9: Rule B2 — Filament mapping                                                        │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/b2_filament_mapping.py                                              │
     │ - Create: tests/test_rules_b2.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_b2.py                                                                  │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.b2_filament_mapping import rule                                          │
     │                                                                                           │
     │ def test_missing_filament_map_fails():                                                    │
     │     ctx = RuleContext(                                                                    │
     │         settings={"filament_colour": ["#FF0000", "#00FF00"]},                             │
     │         filament_keys=["Metadata/filament_settings_0.config"],                            │
     │         filament_settings=[{"filament_type": "PLA"}],                                     │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert results[0].severity == Severity.fail                                           │
     │     assert results[0].fixer_id == "fix_filament_mapping"                                  │
     │                                                                                           │
     │ def test_valid_filament_map_passes():                                                     │
     │     ctx = RuleContext(                                                                    │
     │         settings={"filament_map": [1, 2]},                                                │
     │         filament_keys=["Metadata/filament_settings_0.config", "Metadata/filament_settings_1.config"],                                                                                       │
     │         filament_settings=[{"filament_type": "PLA"}, {"filament_type": "PETG"}],          │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ def test_filament_map_out_of_range_fails():                                               │
     │     ctx = RuleContext(                                                                    │
     │         settings={"filament_map": [1, 5]},  # 5 is out of range 1-4                       │
     │         filament_keys=["Metadata/filament_settings_0.config", "Metadata/filament_settings_1.config"],                                                                                       │
     │         filament_settings=[{"filament_type": "PLA"}, {"filament_type": "PETG"}],          │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert results[0].fixer_id == "fix_filament_mapping"                                  │
     │                                                                                           │
     │ def test_b1_more_than_4_filaments():                                                      │
     │     """B1: >4 filaments is a report-only fail with no fixer."""                           │
     │     ctx = RuleContext(                                                                    │
     │         settings={"filament_map": [1, 2, 3, 4, 5]},                                       │
     │         filament_keys=[f"Metadata/filament_settings_{i}.config" for i in range(5)],       │
     │         filament_settings=[{"filament_type": "PLA"}] * 5,                                 │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     b1_results = [r for r in results if r.rule_id == "B1"]                                │
     │     assert len(b1_results) == 1                                                           │
     │     assert b1_results[0].fixer_id is None                                                 │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/b2_filament_mapping.py                                                      │
     │ """B2 — filament extruder mapping (fail, fixer=fix_filament_mapping). B1 embedded here."""│
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ _MAX_TOOLS = 4                                                                            │
     │                                                                                           │
     │                                                                                           │
     │ class B2Rule:                                                                             │
     │     id = "B2"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         results: list[Result] = []                                                        │
     │         filament_count = len(ctx.filament_settings) or len(ctx.filament_keys)             │
     │                                                                                           │
     │         # B1 check (report-only, no fixer)                                                │
     │         if filament_count > _MAX_TOOLS:                                                   │
     │             results.append(Result(                                                        │
     │                 rule_id="B1",                                                             │
     │                 severity=Severity.fail,                                                   │
     │                 message=f"File has {filament_count} filaments but U1 supports max {_MAX_TOOLS}. "                                                                                           │
     │                         "Manual merge required (Phase 2).",                               │
     │                 fixer_id=None,                                                            │
     │             ))                                                                            │
     │                                                                                           │
     │         filament_map = ctx.settings.get("filament_map")                                   │
     │                                                                                           │
     │         if not filament_map:                                                              │
     │             results.append(Result(                                                        │
     │                 rule_id=self.id,                                                          │
     │                 severity=Severity.fail,                                                   │
     │                 message="No filament_map found. Extruder assignments missing.",           │
     │                 fixer_id="fix_filament_mapping",                                          │
     │             ))                                                                            │
     │             return results                                                                │
     │                                                                                           │
     │         invalid = [i for i, v in enumerate(filament_map) if not (1 <= int(v) <= _MAX_TOOLS)]                                                                                                │
     │         if invalid:                                                                       │
     │             results.append(Result(                                                        │
     │                 rule_id=self.id,                                                          │
     │                 severity=Severity.fail,                                                   │
     │                 message=f"filament_map entries at indices {invalid} are outside range 1–{_MAX_TOOLS}: "                                                                                     │
     │                         f"{[filament_map[i] for i in invalid]}",                          │
     │                 fixer_id="fix_filament_mapping",                                          │
     │             ))                                                                            │
     │                                                                                           │
     │         return results                                                                    │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(B2Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests, commit                                                                 │
     │                                                                                           │
     │ pytest tests/test_rules_b2.py -v                                                          │
     │ git add u1kit/rules/b2_filament_mapping.py tests/test_rules_b2.py                         │
     │ git commit -m "feat(rule): B2 filament mapping + B1 report-only"                          │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 10: Rule B3 — BBL-specific fields                                                    │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/b3_bbl_fields.py                                                    │
     │ - Create: tests/test_rules_b3.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_b3.py                                                                  │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.b3_bbl_fields import rule                                                │
     │                                                                                           │
     │ def test_bbl_filament_extruder_variant_warns():                                           │
     │     ctx = RuleContext(                                                                    │
     │         settings={},                                                                      │
     │         filament_keys=["Metadata/filament_settings_0.config"],                            │
     │         filament_settings=[{"filament_extruder_variant": "BBL_Hardened_0.4"}],            │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert any(r.severity == Severity.warn for r in results)                              │
     │     assert any(r.fixer_id == "fix_bbl_fields" for r in results)                           │
     │                                                                                           │
     │ def test_bambu_compatible_printers_warns():                                               │
     │     ctx = RuleContext(                                                                    │
     │         settings={"compatible_printers": ["Bambu Lab X1 Carbon", "Bambu Lab P1S"]},       │
     │         filament_keys=[],                                                                 │
     │         filament_settings=[],                                                             │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) >= 1                                                              │
     │     assert all(r.fixer_id == "fix_bbl_fields" for r in results)                           │
     │                                                                                           │
     │ def test_clean_file_passes():                                                             │
     │     ctx = RuleContext(                                                                    │
     │         settings={"compatible_printers": ["SnapmakerU1"]},                                │
     │         filament_keys=[],                                                                 │
     │         filament_settings=[{"filament_type": "PLA"}],                                     │
     │     )                                                                                     │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/b3_bbl_fields.py                                                            │
     │ """B3 — BBL-specific filament/printer fields (warn, fixer=fix_bbl_fields)."""             │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ _BBL_FILAMENT_KEYS = {"filament_extruder_variant", "inherits"}                            │
     │ _U1_PRINTER_HINT = "snapmaker"                                                            │
     │                                                                                           │
     │                                                                                           │
     │ class B3Rule:                                                                             │
     │     id = "B3"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         results: list[Result] = []                                                        │
     │                                                                                           │
     │         # Check filament settings for BBL-specific keys                                   │
     │         for i, fs in enumerate(ctx.filament_settings):                                    │
     │             for key in _BBL_FILAMENT_KEYS:                                                │
     │                 if key in fs:                                                             │
     │                     val = fs[key]                                                         │
     │                     if key == "inherits" and _U1_PRINTER_HINT in str(val).lower():        │
     │                         continue  # already U1-compatible                                 │
     │                     results.append(Result(                                                │
     │                         rule_id=self.id,                                                  │
     │                         severity=Severity.warn,                                           │
     │                         message=f"Filament {i}: BBL-specific key {key!r}={val!r} should beremoved",                                                                                         │
     │                         fixer_id="fix_bbl_fields",                                        │
     │                     ))                                                                    │
     │                                                                                           │
     │         # Check compatible_printers                                                       │
     │         compat = ctx.settings.get("compatible_printers", [])                              │
     │         bbl_printers = [p for p in compat if _U1_PRINTER_HINT not in p.lower()]           │
     │         if bbl_printers:                                                                  │
     │             results.append(Result(                                                        │
     │                 rule_id=self.id,                                                          │
     │                 severity=Severity.warn,                                                   │
     │                 message=f"compatible_printers contains non-U1 entries: {bbl_printers}",   │
     │                 fixer_id="fix_bbl_fields",                                                │
     │             ))                                                                            │
     │                                                                                           │
     │         return results                                                                    │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(B3Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests, commit                                                                 │
     │                                                                                           │
     │ pytest tests/test_rules_b3.py -v                                                          │
     │ git add u1kit/rules/b3_bbl_fields.py tests/test_rules_b3.py                               │
     │ git commit -m "feat(rule): B3 BBL-specific field detection"                               │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 11: Rule D1 — Mixed height bounds                                                    │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/rules/d1_mixed_height_bounds.py                                           │
     │ - Create: tests/test_rules_d1.py                                                          │
     │                                                                                           │
     │ Step 1: Write failing tests                                                               │
     │                                                                                           │
     │ # tests/test_rules_d1.py                                                                  │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules.d1_mixed_height_bounds import rule                                       │
     │                                                                                           │
     │ def make_ctx(settings: dict, uniform_height: float = 0.2) -> RuleContext:                 │
     │     return RuleContext(                                                                   │
     │         settings=settings,                                                                │
     │         filament_keys=[],                                                                 │
     │         filament_settings=[],                                                             │
     │         uniform_height=uniform_height,                                                    │
     │     )                                                                                     │
     │                                                                                           │
     │ def test_lower_bound_below_layer_height_fails():                                          │
     │     ctx = make_ctx({                                                                      │
     │         "layer_height": "0.2",                                                            │
     │         "mixed_filament_height_lower_bound": "0.04",                                      │
     │         "mixed_filament_height_upper_bound": "0.35",                                      │
     │     })                                                                                    │
     │     results = rule.check(ctx)                                                             │
     │     assert len(results) == 1                                                              │
     │     assert results[0].severity == Severity.fail                                           │
     │     assert results[0].fixer_id == "fix_mixed_height_bounds"                               │
     │                                                                                           │
     │ def test_bounds_ok_passes():                                                              │
     │     ctx = make_ctx({                                                                      │
     │         "layer_height": "0.2",                                                            │
     │         "mixed_filament_height_lower_bound": "0.2",                                       │
     │         "mixed_filament_height_upper_bound": "0.35",                                      │
     │     })                                                                                    │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ def test_no_mixed_height_keys_skips():                                                    │
     │     ctx = make_ctx({"layer_height": "0.2"})                                               │
     │     results = rule.check(ctx)                                                             │
     │     assert results == []                                                                  │
     │                                                                                           │
     │ def test_diff_preview_shows_target():                                                     │
     │     ctx = make_ctx({                                                                      │
     │         "layer_height": "0.2",                                                            │
     │         "mixed_filament_height_lower_bound": "0.04",                                      │
     │         "mixed_filament_height_upper_bound": "0.35",                                      │
     │     }, uniform_height=0.2)                                                                │
     │     results = rule.check(ctx)                                                             │
     │     assert "0.2" in results[0].diff_preview                                               │
     │                                                                                           │
     │ Step 2: Implement                                                                         │
     │                                                                                           │
     │ # u1kit/rules/d1_mixed_height_bounds.py                                                   │
     │ """D1 — mixed_filament_height bounds vs layer_height (fail, fixer=fix_mixed_height_bounds)."""                                                                                              │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from u1kit.rules import register                                                          │
     │ from u1kit.rules.base import Result, RuleContext, Severity                                │
     │                                                                                           │
     │ _LOWER = "mixed_filament_height_lower_bound"                                              │
     │ _UPPER = "mixed_filament_height_upper_bound"                                              │
     │ _LAYER = "layer_height"                                                                   │
     │                                                                                           │
     │                                                                                           │
     │ class D1Rule:                                                                             │
     │     id = "D1"                                                                             │
     │                                                                                           │
     │     def check(self, ctx: RuleContext) -> list[Result]:                                    │
     │         if _LOWER not in ctx.settings:                                                    │
     │             return []                                                                     │
     │                                                                                           │
     │         lower = float(ctx.settings.get(_LOWER, 0))                                        │
     │         layer = float(ctx.settings.get(_LAYER, 0))                                        │
     │         upper = float(ctx.settings.get(_UPPER, 0))                                        │
     │                                                                                           │
     │         if lower >= layer:                                                                │
     │             return []                                                                     │
     │                                                                                           │
     │         target = ctx.uniform_height                                                       │
     │         diff = (                                                                          │
     │             f"{_LAYER}: {layer} → {target}\n"                                             │
     │             f"{_LOWER}: {lower} → {target}\n"                                             │
     │             f"{_UPPER}: {upper} → {target}"                                               │
     │         )                                                                                 │
     │         return [Result(                                                                   │
     │             rule_id=self.id,                                                              │
     │             severity=Severity.fail,                                                       │
     │             message=f"{_LOWER}={lower} < {_LAYER}={layer}. "                              │
     │                     f"All three will be locked to uniform_height={target}.",              │
     │             fixer_id="fix_mixed_height_bounds",                                           │
     │             diff_preview=diff,                                                            │
     │         )]                                                                                │
     │                                                                                           │
     │                                                                                           │
     │ rule = register(D1Rule())                                                                 │
     │                                                                                           │
     │ Step 3: Run tests, commit                                                                 │
     │                                                                                           │
     │ pytest tests/test_rules_d1.py -v                                                          │
     │ git add u1kit/rules/d1_mixed_height_bounds.py tests/test_rules_d1.py                      │
     │ git commit -m "feat(rule): D1 mixed height bounds validation"                             │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 12: Fixer base + pipeline                                                            │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/fixers/base.py                                                            │
     │ - Create: u1kit/fixers/__init__.py                                                        │
     │                                                                                           │
     │ Step 1: fixers/base.py                                                                    │
     │                                                                                           │
     │ # u1kit/fixers/base.py                                                                    │
     │ """Fixer protocol and FixerContext."""                                                    │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from dataclasses import dataclass                                                         │
     │ from typing import Any, Protocol                                                          │
     │                                                                                           │
     │                                                                                           │
     │ @dataclass                                                                                │
     │ class FixerContext:                                                                       │
     │     settings: dict[str, Any]                                                              │
     │     filament_keys: list[str]                                                              │
     │     filament_settings: list[dict[str, Any]]                                               │
     │     uniform_height: float = 0.2                                                           │
     │                                                                                           │
     │                                                                                           │
     │ class Fixer(Protocol):                                                                    │
     │     id: str                                                                               │
     │                                                                                           │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         ...                                                                               │
     │                                                                                           │
     │ Step 2: fixers/init.py — registry + pipeline                                              │
     │                                                                                           │
     │ # u1kit/fixers/__init__.py                                                                │
     │ """Fixer registry and pipeline (dry-run / auto / interactive)."""                         │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ from enum import Enum                                                                     │
     │ from typing import TYPE_CHECKING                                                          │
     │                                                                                           │
     │ if TYPE_CHECKING:                                                                         │
     │     from u1kit.fixers.base import Fixer, FixerContext                                     │
     │     from u1kit.rules.base import Result                                                   │
     │                                                                                           │
     │ _REGISTRY: dict[str, "Fixer"] = {}                                                        │
     │                                                                                           │
     │                                                                                           │
     │ class RunMode(str, Enum):                                                                 │
     │     dry_run = "dry-run"                                                                   │
     │     auto = "auto"                                                                         │
     │     interactive = "interactive"                                                           │
     │                                                                                           │
     │                                                                                           │
     │ def register(fixer: "Fixer") -> "Fixer":                                                  │
     │     _REGISTRY[fixer.id] = fixer                                                           │
     │     return fixer                                                                          │
     │                                                                                           │
     │                                                                                           │
     │ def get(fixer_id: str) -> "Fixer":                                                        │
     │     return _REGISTRY[fixer_id]                                                            │
     │                                                                                           │
     │                                                                                           │
     │ def run_pipeline(                                                                         │
     │     results: list["Result"],                                                              │
     │     ctx: "FixerContext",                                                                  │
     │     mode: RunMode = RunMode.dry_run,                                                      │
     │ ) -> list[str]:                                                                           │
     │     """Apply fixers for all fixable results. Returns list of applied fixer IDs."""        │
     │     applied: list[str] = []                                                               │
     │     fixable = [r for r in results if r.fixer_id is not None]                              │
     │                                                                                           │
     │     for result in fixable:                                                                │
     │         fixer_id = result.fixer_id                                                        │
     │         assert fixer_id is not None                                                       │
     │         if fixer_id not in _REGISTRY:                                                     │
     │             continue                                                                      │
     │                                                                                           │
     │         if mode == RunMode.dry_run:                                                       │
     │             applied.append(f"[dry-run] {fixer_id}: {result.message}")                     │
     │             continue                                                                      │
     │                                                                                           │
     │         if mode == RunMode.interactive:                                                   │
     │             _prompt_and_apply(result, ctx, applied)                                       │
     │         else:  # auto                                                                     │
     │             _REGISTRY[fixer_id].apply(ctx)                                                │
     │             applied.append(fixer_id)                                                      │
     │                                                                                           │
     │     return applied                                                                        │
     │                                                                                           │
     │                                                                                           │
     │ def _prompt_and_apply(                                                                    │
     │     result: "Result",                                                                     │
     │     ctx: "FixerContext",                                                                  │
     │     applied: list[str],                                                                   │
     │ ) -> None:                                                                                │
     │     try:                                                                                  │
     │         from prompt_toolkit import prompt as pt_prompt                                    │
     │     except ImportError:                                                                   │
     │         import builtins                                                                   │
     │         pt_prompt = lambda msg: builtins.input(msg)  # type: ignore[assignment]           │
     │                                                                                           │
     │     fixer_id = result.fixer_id                                                            │
     │     assert fixer_id is not None                                                           │
     │     if result.diff_preview:                                                               │
     │         print(f"\n{result.diff_preview}")                                                 │
     │     answer = pt_prompt(f"Apply {fixer_id}? [{result.message[:60]}] [y/N] ")               │
     │     if answer.strip().lower() == "y":                                                     │
     │         _REGISTRY[fixer_id].apply(ctx)                                                    │
     │         applied.append(fixer_id)                                                          │
     │                                                                                           │
     │                                                                                           │
     │ # Import fixers to trigger registration                                                   │
     │ from u1kit.fixers.fix_printer_profile import fixer as _f_a2  # noqa: E402, F401           │
     │ from u1kit.fixers.fix_toolchange_gcode import fixer as _f_a3  # noqa: E402, F401          │
     │ from u1kit.fixers.fix_filament_mapping import fixer as _f_b2  # noqa: E402, F401          │
     │ from u1kit.fixers.fix_bbl_fields import fixer as _f_b3  # noqa: E402, F401                │
     │ from u1kit.fixers.fix_mixed_height_bounds import fixer as _f_d1  # noqa: E402, F401       │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/fixers/base.py u1kit/fixers/__init__.py                                     │
     │ git commit -m "feat: fixer base types, registry, and pipeline (dry-run/auto/interactive)" │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 13: Individual fixers                                                                │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/fixers/fix_printer_profile.py                                             │
     │ - Create: u1kit/fixers/fix_toolchange_gcode.py                                            │
     │ - Create: u1kit/fixers/fix_filament_mapping.py                                            │
     │ - Create: u1kit/fixers/fix_bbl_fields.py                                                  │
     │ - Create: u1kit/fixers/fix_mixed_height_bounds.py                                         │
     │ - Create: tests/test_fixers.py                                                            │
     │                                                                                           │
     │ Step 1: Write tests for all fixers                                                        │
     │                                                                                           │
     │ # tests/test_fixers.py                                                                    │
     │ import pytest                                                                             │
     │ from u1kit.fixers.base import FixerContext                                                │
     │ import u1kit.fixers  # trigger registration                                               │
     │                                                                                           │
     │ def base_ctx(**overrides) -> FixerContext:                                                │
     │     defaults = dict(settings={}, filament_keys=[], filament_settings=[], uniform_height=0.2)                                                                                                │
     │     defaults.update(overrides)                                                            │
     │     return FixerContext(**defaults)  # type: ignore[arg-type]                             │
     │                                                                                           │
     │ # --- fix_printer_profile ---                                                             │
     │ def test_fix_printer_profile_rewrites_keys():                                             │
     │     from u1kit.fixers.fix_printer_profile import fixer                                    │
     │     ctx = base_ctx(settings={"printer_settings_id": "Bambu X1C", "printer_model": "BambuLaX1C"})                                                                                            │
     │     fixer.apply(ctx)                                                                      │
     │     assert ctx.settings["printer_settings_id"] == "Snapmaker U1 0.4 nozzle"               │
     │     assert ctx.settings["printer_model"] == "SnapmakerU1"                                 │
     │                                                                                           │
     │ # --- fix_toolchange_gcode ---                                                            │
     │ def test_fix_toolchange_gcode_strips_M620():                                              │
     │     from u1kit.fixers.fix_toolchange_gcode import fixer                                   │
     │     ctx = base_ctx(settings={                                                             │
     │         "change_filament_gcode": "M620 S{next_extruder}A\nM621 S{next_extruder}A",        │
     │         "machine_start_gcode": "G28",                                                     │
     │         "machine_end_gcode": "M104 S0",                                                   │
     │         "layer_change_gcode": "",                                                         │
     │     })                                                                                    │
     │     fixer.apply(ctx)                                                                      │
     │     gcode = ctx.settings["change_filament_gcode"]                                         │
     │     assert "M620" not in gcode                                                            │
     │     assert "M621" not in gcode                                                            │
     │                                                                                           │
     │ # --- fix_filament_mapping ---                                                            │
     │ def test_fix_filament_mapping_assigns_by_first_use():                                     │
     │     from u1kit.fixers.fix_filament_mapping import fixer                                   │
     │     ctx = base_ctx(                                                                       │
     │         settings={},                                                                      │
     │         filament_keys=["Metadata/filament_settings_0.config", "Metadata/filament_settings_1.config"],                                                                                       │
     │         filament_settings=[{"filament_type": "PLA"}, {"filament_type": "PETG"}],          │
     │     )                                                                                     │
     │     fixer.apply(ctx)                                                                      │
     │     assert ctx.settings["filament_map"] == [1, 2]                                         │
     │                                                                                           │
     │ # --- fix_bbl_fields ---                                                                  │
     │ def test_fix_bbl_fields_removes_extruder_variant():                                       │
     │     from u1kit.fixers.fix_bbl_fields import fixer                                         │
     │     ctx = base_ctx(                                                                       │
     │         filament_keys=["Metadata/filament_settings_0.config"],                            │
     │         filament_settings=[{"filament_type": "PLA", "filament_extruder_variant": "BBL_Hardened_0.4"}],                                                                                      │
     │     )                                                                                     │
     │     fixer.apply(ctx)                                                                      │
     │     assert "filament_extruder_variant" not in ctx.filament_settings[0]                    │
     │                                                                                           │
     │ # --- fix_mixed_height_bounds ---                                                         │
     │ def test_fix_mixed_height_bounds_locks_to_uniform():                                      │
     │     from u1kit.fixers.fix_mixed_height_bounds import fixer                                │
     │     ctx = base_ctx(                                                                       │
     │         settings={                                                                        │
     │             "layer_height": "0.2",                                                        │
     │             "mixed_filament_height_lower_bound": "0.04",                                  │
     │             "mixed_filament_height_upper_bound": "0.35",                                  │
     │         },                                                                                │
     │         uniform_height=0.2,                                                               │
     │     )                                                                                     │
     │     fixer.apply(ctx)                                                                      │
     │     assert ctx.settings["layer_height"] == "0.2"                                          │
     │     assert ctx.settings["mixed_filament_height_lower_bound"] == "0.2"                     │
     │     assert ctx.settings["mixed_filament_height_upper_bound"] == "0.2"                     │
     │                                                                                           │
     │ Step 2: Implement each fixer                                                              │
     │                                                                                           │
     │ # u1kit/fixers/fix_printer_profile.py                                                     │
     │ from __future__ import annotations                                                        │
     │ import json                                                                               │
     │ from importlib.resources import files                                                     │
     │ from u1kit.fixers import register                                                         │
     │ from u1kit.fixers.base import Fixer, FixerContext                                         │
     │                                                                                           │
     │ _COPY_KEYS = [                                                                            │
     │     "printer_settings_id", "printer_model", "printable_area", "printable_height",         │
     │     "machine_max_acceleration_e", "machine_max_acceleration_extruding",                   │
     │     "machine_max_acceleration_retracting", "machine_max_acceleration_travel",             │
     │     "machine_max_acceleration_x", "machine_max_acceleration_y", "machine_max_acceleration_z",                                                                                               │
     │     "machine_max_jerk_e", "machine_max_jerk_x", "machine_max_jerk_y", "machine_max_jerk_z"│
     │     "machine_max_speed_e", "machine_max_speed_x", "machine_max_speed_y", "machine_max_speed_z",                                                                                             │
     │ ]                                                                                         │
     │                                                                                           │
     │ def _load_ref() -> dict:                                                                  │
     │     return json.loads(files("u1kit.data").joinpath("u1_printer_reference.json").read_text())                                                                                                │
     │                                                                                           │
     │ class FixPrinterProfile:                                                                  │
     │     id = "fix_printer_profile"                                                            │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         ref = _load_ref()                                                                 │
     │         for key in _COPY_KEYS:                                                            │
     │             if key in ref and not key.startswith("_"):                                    │
     │                 ctx.settings[key] = ref[key]                                              │
     │                                                                                           │
     │ fixer = register(FixPrinterProfile())                                                     │
     │                                                                                           │
     │ # u1kit/fixers/fix_toolchange_gcode.py                                                    │
     │ from __future__ import annotations                                                        │
     │ import re                                                                                 │
     │ from importlib.resources import files                                                     │
     │ from u1kit.fixers import register                                                         │
     │ from u1kit.fixers.base import FixerContext                                                │
     │                                                                                           │
     │ _GCODE_FIELDS = ("machine_start_gcode", "machine_end_gcode", "change_filament_gcode", "layer_change_gcode")                                                                                 │
     │ _BAMBU_LINE_PATTERNS = [re.compile(r".*\bM62[013]\b.*"), re.compile(r".*\bAMS\b.*", re.IGNORECASE)]                                                                                         │
     │                                                                                           │
     │ def _strip_bambu_lines(gcode: str) -> str:                                                │
     │     lines = gcode.splitlines()                                                            │
     │     clean = [l for l in lines if not any(p.match(l) for p in _BAMBU_LINE_PATTERNS)]       │
     │     return "\n".join(clean)                                                               │
     │                                                                                           │
     │ def _load_toolchange() -> str:                                                            │
     │     return files("u1kit.data").joinpath("u1_toolchange.gcode").read_text()                │
     │                                                                                           │
     │ class FixToolchangeGcode:                                                                 │
     │     id = "fix_toolchange_gcode"                                                           │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         toolchange = _load_toolchange()                                                   │
     │         for field in _GCODE_FIELDS:                                                       │
     │             if field in ctx.settings:                                                     │
     │                 ctx.settings[field] = _strip_bambu_lines(ctx.settings[field])             │
     │         # Replace change_filament_gcode with the U1 template                              │
     │         ctx.settings["change_filament_gcode"] = toolchange                                │
     │                                                                                           │
     │ fixer = register(FixToolchangeGcode())                                                    │
     │                                                                                           │
     │ # u1kit/fixers/fix_filament_mapping.py                                                    │
     │ from __future__ import annotations                                                        │
     │ from u1kit.fixers import register                                                         │
     │ from u1kit.fixers.base import FixerContext                                                │
     │                                                                                           │
     │ class FixFilamentMapping:                                                                 │
     │     id = "fix_filament_mapping"                                                           │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         n = len(ctx.filament_settings) or len(ctx.filament_keys)                          │
     │         # Assign by first-use order: filament 0 → extruder 1, etc.                        │
     │         ctx.settings["filament_map"] = list(range(1, min(n, 4) + 1))                      │
     │                                                                                           │
     │ fixer = register(FixFilamentMapping())                                                    │
     │                                                                                           │
     │ # u1kit/fixers/fix_bbl_fields.py                                                          │
     │ from __future__ import annotations                                                        │
     │ from u1kit.fixers import register                                                         │
     │ from u1kit.fixers.base import FixerContext                                                │
     │                                                                                           │
     │ _REMOVE_FILAMENT_KEYS = {"filament_extruder_variant"}                                     │
     │ _U1_HINT = "snapmaker"                                                                    │
     │                                                                                           │
     │ class FixBblFields:                                                                       │
     │     id = "fix_bbl_fields"                                                                 │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         for fs in ctx.filament_settings:                                                  │
     │             for key in _REMOVE_FILAMENT_KEYS:                                             │
     │                 fs.pop(key, None)                                                         │
     │             # Clean inherits chains pointing to Bambu                                     │
     │             if "inherits" in fs and _U1_HINT not in str(fs["inherits"]).lower():          │
     │                 del fs["inherits"]                                                        │
     │         # Remove non-U1 compatible_printers entries                                       │
     │         compat = ctx.settings.get("compatible_printers", [])                              │
     │         ctx.settings["compatible_printers"] = [                                           │
     │             p for p in compat if _U1_HINT in p.lower()                                    │
     │         ]                                                                                 │
     │                                                                                           │
     │ fixer = register(FixBblFields())                                                          │
     │                                                                                           │
     │ # u1kit/fixers/fix_mixed_height_bounds.py                                                 │
     │ from __future__ import annotations                                                        │
     │ from u1kit.fixers import register                                                         │
     │ from u1kit.fixers.base import FixerContext                                                │
     │                                                                                           │
     │ class FixMixedHeightBounds:                                                               │
     │     id = "fix_mixed_height_bounds"                                                        │
     │     def apply(self, ctx: FixerContext) -> None:                                           │
     │         target = str(ctx.uniform_height)                                                  │
     │         ctx.settings["layer_height"] = target                                             │
     │         ctx.settings["mixed_filament_height_lower_bound"] = target                        │
     │         ctx.settings["mixed_filament_height_upper_bound"] = target                        │
     │                                                                                           │
     │ fixer = register(FixMixedHeightBounds())                                                  │
     │                                                                                           │
     │ Step 3: Run tests                                                                         │
     │                                                                                           │
     │ pytest tests/test_fixers.py -v                                                            │
     │                                                                                           │
     │ Expected: all PASS                                                                        │
     │                                                                                           │
     │ Step 4: Commit                                                                            │
     │                                                                                           │
     │ git add u1kit/fixers/                                                                     │
     │ git commit -m "feat: all Phase 1 fixers (A2, A3, B2, B3, D1)"                             │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 14: report.py                                                                        │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/report.py                                                                 │
     │                                                                                           │
     │ # u1kit/report.py                                                                         │
     │ """JSON and human-readable report formatters."""                                          │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ import json                                                                               │
     │ from dataclasses import asdict                                                            │
     │ from typing import Any                                                                    │
     │                                                                                           │
     │ from u1kit.rules.base import Result, Severity                                             │
     │                                                                                           │
     │ _SEVERITY_ICON = {                                                                        │
     │     Severity.fail: "✗",                                                                   │
     │     Severity.warn: "⚠",                                                                   │
     │     Severity.info: "ℹ",                                                                   │
     │ }                                                                                         │
     │                                                                                           │
     │                                                                                           │
     │ def to_json(results: list[Result], applied_fixers: list[str] | None = None) -> str:       │
     │     data: dict[str, Any] = {                                                              │
     │         "schema_version": "1.0",                                                          │
     │         "results": [                                                                      │
     │             {                                                                             │
     │                 "rule_id": r.rule_id,                                                     │
     │                 "severity": r.severity.value,                                             │
     │                 "message": r.message,                                                     │
     │                 "fixer_id": r.fixer_id,                                                   │
     │                 "diff_preview": r.diff_preview,                                           │
     │             }                                                                             │
     │             for r in results                                                              │
     │         ],                                                                                │
     │         "summary": {                                                                      │
     │             "fail": sum(1 for r in results if r.severity == Severity.fail),               │
     │             "warn": sum(1 for r in results if r.severity == Severity.warn),               │
     │             "info": sum(1 for r in results if r.severity == Severity.info),               │
     │         },                                                                                │
     │     }                                                                                     │
     │     if applied_fixers is not None:                                                        │
     │         data["applied_fixers"] = applied_fixers                                           │
     │     return json.dumps(data, indent=2)                                                     │
     │                                                                                           │
     │                                                                                           │
     │ def to_text(results: list[Result], applied_fixers: list[str] | None = None) -> str:       │
     │     lines: list[str] = []                                                                 │
     │     for r in results:                                                                     │
     │         icon = _SEVERITY_ICON.get(r.severity, "?")                                        │
     │         lines.append(f"  {icon} [{r.rule_id}] {r.message}")                               │
     │         if r.diff_preview:                                                                │
     │             for dl in r.diff_preview.splitlines():                                        │
     │                 lines.append(f"      {dl}")                                               │
     │     lines.append("")                                                                      │
     │     fail = sum(1 for r in results if r.severity == Severity.fail)                         │
     │     warn = sum(1 for r in results if r.severity == Severity.warn)                         │
     │     lines.append(f"  Summary: {fail} fail, {warn} warn, {len(results)-fail-warn} info")   │
     │     if applied_fixers:                                                                    │
     │         lines.append(f"  Applied fixers: {', '.join(applied_fixers)}")                    │
     │     return "\n".join(lines)                                                               │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/report.py                                                                   │
     │ git commit -m "feat: report.py JSON and text formatters"                                  │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 15: Presets                                                                          │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/presets/bambu_to_u1.yaml                                                  │
     │                                                                                           │
     │ # u1kit/presets/bambu_to_u1.yaml                                                          │
     │ name: bambu-to-u1                                                                         │
     │ description: "Convert Bambu/Makerworld .3mf for Snapmaker U1"                             │
     │ active_rules:                                                                             │
     │   - A1  # prerequisite — always runs first                                                │
     │   - A2                                                                                    │
     │   - A3                                                                                    │
     │   - B1  # report-only, no fixer                                                           │
     │   - B2                                                                                    │
     │   - B3                                                                                    │
     │ # D1 is always checked regardless of preset (height safety)                               │
     │ options:                                                                                  │
     │   uniform_height: 0.2                                                                     │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/presets/                                                                    │
     │ git commit -m "chore: add bambu-to-u1 preset"                                             │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 16: CLI                                                                              │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: u1kit/cli.py                                                                    │
     │                                                                                           │
     │ # u1kit/cli.py                                                                            │
     │ """CLI entry point: u1kit lint / fix / presets."""                                        │
     │ from __future__ import annotations                                                        │
     │                                                                                           │
     │ import json                                                                               │
     │ import sys                                                                                │
     │ from pathlib import Path                                                                  │
     │ from typing import Any                                                                    │
     │                                                                                           │
     │ import click                                                                              │
     │ import yaml                                                                               │
     │ from importlib.resources import files                                                     │
     │                                                                                           │
     │ import u1kit.rules  # trigger rule registration                                           │
     │ import u1kit.fixers  # trigger fixer registration                                         │
     │ from u1kit.archive import Archive3mf                                                      │
     │ from u1kit.config import ProjectConfig                                                    │
     │ from u1kit.fixers import RunMode, run_pipeline                                            │
     │ from u1kit.fixers.base import FixerContext                                                │
     │ from u1kit.report import to_json, to_text                                                 │
     │ from u1kit.rules.base import RuleContext, Severity                                        │
     │ from u1kit.rules import all_rules, get as get_rule                                        │
     │                                                                                           │
     │                                                                                           │
     │ def _load_preset(name: str) -> dict[str, Any]:                                            │
     │     preset_data = files("u1kit.presets").joinpath(f"{name}.yaml").read_text()             │
     │     return yaml.safe_load(preset_data)                                                    │
     │                                                                                           │
     │                                                                                           │
     │ def _run_rules(cfg: ProjectConfig, rule_ids: list[str], uniform_height: float):           │
     │     ctx = RuleContext(                                                                    │
     │         settings=cfg.settings,                                                            │
     │         filament_keys=cfg.filament_keys,                                                  │
     │         filament_settings=cfg.filament_settings,                                          │
     │         uniform_height=uniform_height,                                                    │
     │     )                                                                                     │
     │     results = []                                                                          │
     │     for rid in rule_ids:                                                                  │
     │         try:                                                                              │
     │             rule = get_rule(rid)                                                          │
     │         except KeyError:                                                                  │
     │             click.echo(f"Warning: unknown rule {rid!r}", err=True)                        │
     │             continue                                                                      │
     │         results.extend(rule.check(ctx))                                                   │
     │     # D1 always runs                                                                      │
     │     if "D1" not in rule_ids:                                                              │
     │         results.extend(get_rule("D1").check(ctx))                                         │
     │     return results, ctx                                                                   │
     │                                                                                           │
     │                                                                                           │
     │ @click.group()                                                                            │
     │ def main() -> None:                                                                       │
     │     """u1kit — Convert Bambu .3mf for Snapmaker U1."""                                    │
     │                                                                                           │
     │                                                                                           │
     │ @main.command()                                                                           │
     │ @click.argument("file", type=click.Path(exists=True, path_type=Path))                     │
     │ @click.option("--json", "as_json", is_flag=True)                                          │
     │ def lint(file: Path, as_json: bool) -> None:                                              │
     │     """Lint a .3mf file against U1 rules."""                                              │
     │     arch = Archive3mf.from_path(file)                                                     │
     │     cfg = ProjectConfig.from_archive(arch)                                                │
     │     preset = _load_preset("bambu-to-u1")                                                  │
     │     rule_ids: list[str] = preset["active_rules"]                                          │
     │     uniform_height: float = preset.get("options", {}).get("uniform_height", 0.2)          │
     │                                                                                           │
     │     results, _ = _run_rules(cfg, rule_ids, uniform_height)                                │
     │                                                                                           │
     │     if as_json:                                                                           │
     │         click.echo(to_json(results))                                                      │
     │     else:                                                                                 │
     │         click.echo(to_text(results))                                                      │
     │                                                                                           │
     │     has_fail = any(r.severity == Severity.fail for r in results)                          │
     │     sys.exit(1 if has_fail else 0)                                                        │
     │                                                                                           │
     │                                                                                           │
     │ @main.command()                                                                           │
     │ @click.argument("file", type=click.Path(exists=True, path_type=Path))                     │
     │ @click.option("--preset", "preset_name", default="bambu-to-u1")                           │
     │ @click.option("--dry-run", is_flag=True)                                                  │
     │ @click.option("--interactive", is_flag=True)                                              │
     │ @click.option("--out", "out_path", type=click.Path(path_type=Path), default=None)         │
     │ @click.option("--uniform-height", type=float, default=None)                               │
     │ @click.option("--json", "as_json", is_flag=True)                                          │
     │ def fix(                                                                                  │
     │     file: Path,                                                                           │
     │     preset_name: str,                                                                     │
     │     dry_run: bool,                                                                        │
     │     interactive: bool,                                                                    │
     │     out_path: Path | None,                                                                │
     │     uniform_height: float | None,                                                         │
     │     as_json: bool,                                                                        │
     │ ) -> None:                                                                                │
     │     """Fix a .3mf file for U1 compatibility."""                                           │
     │     arch = Archive3mf.from_path(file)                                                     │
     │     cfg = ProjectConfig.from_archive(arch)                                                │
     │     preset = _load_preset(preset_name)                                                    │
     │     rule_ids: list[str] = preset["active_rules"]                                          │
     │     uh = uniform_height or preset.get("options", {}).get("uniform_height", 0.2)           │
     │                                                                                           │
     │     results, rule_ctx = _run_rules(cfg, rule_ids, uh)                                     │
     │                                                                                           │
     │     fixer_ctx = FixerContext(                                                             │
     │         settings=cfg.settings,                                                            │
     │         filament_keys=cfg.filament_keys,                                                  │
     │         filament_settings=cfg.filament_settings,                                          │
     │         uniform_height=uh,                                                                │
     │     )                                                                                     │
     │                                                                                           │
     │     if dry_run:                                                                           │
     │         mode = RunMode.dry_run                                                            │
     │     elif interactive:                                                                     │
     │         mode = RunMode.interactive                                                        │
     │     else:                                                                                 │
     │         mode = RunMode.auto                                                               │
     │                                                                                           │
     │     applied = run_pipeline(results, fixer_ctx, mode)                                      │
     │                                                                                           │
     │     # Flush mutated config back to archive                                                │
     │     if mode != RunMode.dry_run:                                                           │
     │         cfg.settings = fixer_ctx.settings                                                 │
     │         cfg.filament_settings = fixer_ctx.filament_settings                               │
     │         cfg.flush(arch)                                                                   │
     │         dest = out_path or file                                                           │
     │         arch.to_path(dest)                                                                │
     │                                                                                           │
     │     if as_json:                                                                           │
     │         click.echo(to_json(results, applied))                                             │
     │     else:                                                                                 │
     │         click.echo(to_text(results, applied))                                             │
     │                                                                                           │
     │                                                                                           │
     │ @main.group()                                                                             │
     │ def presets() -> None:                                                                    │
     │     """Manage conversion presets."""                                                      │
     │                                                                                           │
     │                                                                                           │
     │ @presets.command("list")                                                                  │
     │ @click.option("--json", "as_json", is_flag=True)                                          │
     │ def presets_list(as_json: bool) -> None:                                                  │
     │     """List available presets."""                                                         │
     │     preset = _load_preset("bambu-to-u1")                                                  │
     │     if as_json:                                                                           │
     │         click.echo(json.dumps([preset], indent=2))                                        │
     │     else:                                                                                 │
     │         click.echo(f"  {preset['name']}: {preset['description']}")                        │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add u1kit/cli.py                                                                      │
     │ git commit -m "feat: CLI (lint / fix / presets list)"                                     │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 17: Integration tests + CLI tests                                                    │
     │                                                                                           │
     │ Files:                                                                                    │
     │ - Create: tests/test_cli.py                                                               │
     │                                                                                           │
     │ # tests/test_cli.py                                                                       │
     │ """Integration tests for the full pipeline via CLI."""                                    │
     │ import io, json, zipfile                                                                  │
     │ from pathlib import Path                                                                  │
     │ import pytest                                                                             │
     │ from click.testing import CliRunner                                                       │
     │ from u1kit.cli import main                                                                │
     │ from tests.conftest import make_3mf, MINIMAL_PROJECT_SETTINGS                             │
     │                                                                                           │
     │ BAMBU_4COLOR_SETTINGS = {                                                                 │
     │     "printer_settings_id": "Bambu Lab X1 Carbon 0.4 nozzle",                              │
     │     "printer_model": "BambuLab X1 Carbon",                                                │
     │     "layer_height": "0.2",                                                                │
     │     "filament_map": [1, 2, 3, 4],                                                         │
     │     "machine_start_gcode": "G28",                                                         │
     │     "machine_end_gcode": "M104 S0",                                                       │
     │     "change_filament_gcode": "M620 S{next_extruder}A\nT{next_extruder}\nM621 S{next_extruder}A",                                                                                            │
     │     "layer_change_gcode": "",                                                             │
     │     "compatible_printers": ["Bambu Lab X1 Carbon"],                                       │
     │ }                                                                                         │
     │                                                                                           │
     │ def test_lint_bambu_file_fails(tmp_path):                                                 │
     │     """Bambu file should fail lint with A2 and A3."""                                     │
     │     f = tmp_path / "test.3mf"                                                             │
     │     f.write_bytes(make_3mf(BAMBU_4COLOR_SETTINGS))                                        │
     │     runner = CliRunner()                                                                  │
     │     result = runner.invoke(main, ["lint", str(f)])                                        │
     │     assert result.exit_code == 1                                                          │
     │     assert "A2" in result.output or "A3" in result.output                                 │
     │                                                                                           │
     │ def test_fix_then_lint_passes(tmp_path):                                                  │
     │     """After fix --preset bambu-to-u1, lint should produce no fails."""                   │
     │     src = tmp_path / "src.3mf"                                                            │
     │     out = tmp_path / "out.3mf"                                                            │
     │     src.write_bytes(make_3mf(BAMBU_4COLOR_SETTINGS))                                      │
     │     runner = CliRunner()                                                                  │
     │     fix_result = runner.invoke(main, ["fix", str(src), "--out", str(out)])                │
     │     assert fix_result.exit_code == 0, fix_result.output                                   │
     │                                                                                           │
     │     lint_result = runner.invoke(main, ["lint", str(out)])                                 │
     │     # May still have warns/infos, but no fails                                            │
     │     assert lint_result.exit_code == 0, lint_result.output                                 │
     │                                                                                           │
     │ def test_d1_fix_locks_bounds(tmp_path):                                                   │
     │     """Full Spectrum file: D1 locks all three height fields to uniform_height."""         │
     │     settings = {                                                                          │
     │         **MINIMAL_PROJECT_SETTINGS,                                                       │
     │         "mixed_filament_height_lower_bound": "0.04",                                      │
     │         "mixed_filament_height_upper_bound": "0.35",                                      │
     │         "layer_height": "0.2",                                                            │
     │     }                                                                                     │
     │     src = tmp_path / "fs.3mf"                                                             │
     │     out = tmp_path / "fs_out.3mf"                                                         │
     │     src.write_bytes(make_3mf(settings))                                                   │
     │     runner = CliRunner()                                                                  │
     │     runner.invoke(main, ["fix", str(src), "--out", str(out)])                             │
     │                                                                                           │
     │     # Read output and check bounds                                                        │
     │     arch_out = __import__("u1kit.archive", fromlist=["Archive3mf"]).Archive3mf.from_path(out)                                                                                               │
     │     cfg = arch_out.get_project_settings()                                                 │
     │     assert cfg["mixed_filament_height_lower_bound"] == "0.2"                              │
     │     assert cfg["layer_height"] == "0.2"                                                   │
     │                                                                                           │
     │ def test_lint_json_output(tmp_path):                                                      │
     │     """--json produces valid JSON with schema_version."""                                 │
     │     f = tmp_path / "test.3mf"                                                             │
     │     f.write_bytes(make_3mf(BAMBU_4COLOR_SETTINGS))                                        │
     │     runner = CliRunner()                                                                  │
     │     result = runner.invoke(main, ["lint", str(f), "--json"])                              │
     │     data = json.loads(result.output)                                                      │
     │     assert "schema_version" in data                                                       │
     │     assert "results" in data                                                              │
     │     assert "summary" in data                                                              │
     │                                                                                           │
     │ def test_archive_roundtrip_thumbnail_preserved(tmp_path):                                 │
     │     """Non-config entries survive fix unchanged."""                                       │
     │     FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 128                                       │
     │     src = tmp_path / "with_thumb.3mf"                                                     │
     │     out = tmp_path / "with_thumb_out.3mf"                                                 │
     │     src.write_bytes(make_3mf(BAMBU_4COLOR_SETTINGS, extra_entries={"Metadata/thumbnail.png": FAKE_PNG}))                                                                                    │
     │     runner = CliRunner()                                                                  │
     │     runner.invoke(main, ["fix", str(src), "--out", str(out)])                             │
     │                                                                                           │
     │     with zipfile.ZipFile(out) as zf:                                                      │
     │         assert zf.read("Metadata/thumbnail.png") == FAKE_PNG                              │
     │                                                                                           │
     │ Step: Run all tests                                                                       │
     │                                                                                           │
     │ pytest tests/ -v                                                                          │
     │                                                                                           │
     │ Expected: all PASS (or only known placeholder-related skips)                              │
     │                                                                                           │
     │ Step: Commit                                                                              │
     │                                                                                           │
     │ git add tests/test_cli.py                                                                 │
     │ git commit -m "test: integration tests covering full pipeline"                            │
     │                                                                                           │
     │ ---                                                                                       │
     │ Task 18: Final wiring + README                                                            │
     │                                                                                           │
     │ Step 1: Add __init__.py entries for data and presets packages                             │
     │                                                                                           │
     │ Add u1kit/data/__init__.py and u1kit/presets/__init__.py (empty) so importlib.resources cafind them.                                                                                        │
     │                                                                                           │
     │ Step 2: Run full test suite + type check                                                  │
     │                                                                                           │
     │ pytest tests/ -v                                                                          │
     │ mypy u1kit/ --strict                                                                      │
     │ ruff check u1kit/ tests/                                                                  │
     │                                                                                           │
     │ Fix any issues before proceeding.                                                         │
     │                                                                                           │
     │ Step 3: Update README with exit criteria section                                          │
     │                                                                                           │
     │ ## Exit Criteria                                                                          │
     │                                                                                           │
     │ A Makerworld Bambu 4-color `.3mf`, run through `u1kit fix --preset bambu-to-u1`,          │
     │ opens in Snapmaker Orca without errors. All Phase 1 rules have passing fixture tests.     │
     │ `u1kit lint --json` and `u1kit fix --json` produce stable, documented schemas.            │
     │                                                                                           │
     │ Step 4: Final commit                                                                      │
     │                                                                                           │
     │ git add README.md u1kit/data/__init__.py u1kit/presets/__init__.py                        │
     │ git commit -m "chore: final wiring, README exit criteria, type check clean"               │
     │                                                                                           │
     │ ---                                                                                       │
     │ Verification                                                                              │
     │                                                                                           │
     │ # Install and run the full suite                                                          │
     │ pip install -e ".[dev]"                                                                   │
     │ pytest tests/ -v --tb=short                                                               │
     │                                                                                           │
     │ # Check a synthetic Bambu file end-to-end                                                 │
     │ python -c "                                                                               │
     │ from tests.conftest import make_3mf                                                       │
     │ from pathlib import Path                                                                  │
     │ data = make_3mf({'printer_settings_id':'Bambu Lab X1C 0.4','printer_model':'BambuLab X1C','layer_height':'0.2','filament_map':[1,2],'machine_start_gcode':'G28','machine_end_gcode':'M104 S0','change_filament_gcode':'M620 S1A','layer_change_gcode':''})                                    │
     │ Path('/tmp/test_bambu.3mf').write_bytes(data)                                             │
     │ "                                                                                         │
     │ u1kit lint /tmp/test_bambu.3mf       # should exit 1 (fails)                              │
     │ u1kit fix  /tmp/test_bambu.3mf --out /tmp/test_u1.3mf                                     │
     │ u1kit lint /tmp/test_u1.3mf          # should exit 0 (clean)                              │
     │ u1kit lint /tmp/test_u1.3mf --json   # should print valid JSON                            │
     │                                                                                           │
     │ # Type check + lint                                                                       │
     │ mypy u1kit/ --strict                                                                      │
     │ ruff check u1kit/ tests/     