"""Entry point so ``python -m u1kit`` and PyInstaller one-file builds work.

``python -m u1kit`` invokes this module directly. ``scripts/build_sidecar.py``
passes the path to this file to PyInstaller so the frozen binary's entry
point is ``u1kit.cli.main`` — the same one ``u1kit`` script hook uses.
"""

from __future__ import annotations

from u1kit.cli import main

if __name__ == "__main__":
    main()
