"""Build the u1kit CLI as a single-file sidecar binary via PyInstaller.

The Tauri GUI (Phase 3) invokes the CLI as a subprocess. Tauri's
``tauri-plugin-shell`` can spawn a binary placed in
``gui/src-tauri/resources/sidecar/<target-triple>/u1kit<suffix>``. This
script produces exactly that binary for the current host, in one-file
mode, with the runtime data files (rule docs, printer reference,
presets, toolchange gcode) embedded.

Run from the repo root::

    python scripts/build_sidecar.py

Output goes to ``dist/sidecar/<target-triple>/u1kit[.exe]``. The
resulting binary is self-contained — no Python interpreter needed on
the target machine.

Requires ``pyinstaller`` to be installed (listed in the ``dev`` extra).
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist" / "sidecar"


def target_triple() -> str:
    """Compute the Rust-style target triple for the current host.

    Tauri uses these to namespace sidecar binaries under
    ``resources/sidecar/<triple>/``. We mirror the convention so the
    sidecar drops into the right location.
    """
    arch_map = {
        "x86_64": "x86_64",
        "AMD64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }
    arch = arch_map.get(platform.machine(), platform.machine())

    system = platform.system()
    if system == "Windows":
        return f"{arch}-pc-windows-msvc"
    if system == "Darwin":
        return f"{arch}-apple-darwin"
    if system == "Linux":
        return f"{arch}-unknown-linux-gnu"
    raise RuntimeError(f"Unsupported host platform: {system}")


def build() -> Path:
    """Build the sidecar and return the path to the produced binary."""
    triple = target_triple()
    out_dir = DIST_DIR / triple
    work_dir = DIST_DIR / f".build-{triple}"
    spec_dir = DIST_DIR / f".spec-{triple}"

    # Clean previous artifacts for this triple.
    for d in (out_dir, work_dir, spec_dir):
        if d.exists():
            shutil.rmtree(d)
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = ".exe" if platform.system() == "Windows" else ""
    target_name = "u1kit"

    # Data files that u1kit loads at runtime.
    # PyInstaller's --add-data uses `src<sep>dest` where sep is ; on
    # Windows and : elsewhere.
    sep = ";" if platform.system() == "Windows" else ":"
    data_specs = [
        f"{REPO_ROOT / 'u1kit' / 'data'}{sep}u1kit/data",
        f"{REPO_ROOT / 'u1kit' / 'presets'}{sep}u1kit/presets",
    ]

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        target_name,
        "--distpath",
        str(out_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
        "--noconfirm",
        "--console",
    ]
    for spec in data_specs:
        cmd.extend(["--add-data", spec])
    # Entry point: u1kit's CLI module's main function.
    cmd.append(str(REPO_ROOT / "u1kit" / "__main__.py"))

    print(f"Building sidecar for {triple}...")
    print(f"  Output: {out_dir}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller failed with exit {result.returncode}")

    built = out_dir / f"{target_name}{suffix}"
    if not built.exists():
        raise SystemExit(f"Build finished but {built} is missing")

    # Clean up build/spec directories — only the final binary is kept.
    for d in (work_dir, spec_dir):
        if d.exists():
            shutil.rmtree(d)

    print(f"  Built: {built}")
    return built


def smoke_test(binary: Path) -> None:
    """Run --version on the produced binary and verify it matches the package."""
    expected = pkg_version("u1kit")
    result = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise SystemExit(
            f"Smoke test failed (exit {result.returncode}):\n{result.stderr}"
        )
    reported = result.stdout.strip()
    if reported != expected:
        raise SystemExit(
            f"Version mismatch: binary reports {reported!r}, package is {expected!r}"
        )
    print(f"  Smoke: --version -> {reported!r} OK")


def main() -> None:
    binary = build()
    smoke_test(binary)
    print("Sidecar build complete.")


if __name__ == "__main__":
    main()
