"""Read and write .3mf archives with byte-identical passthrough for non-config entries."""

from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

CONFIG_PATH = "Metadata/project_settings.config"


@dataclass
class ArchiveEntry:
    """A single entry in a .3mf ZIP archive."""

    info: zipfile.ZipInfo
    data: bytes


@dataclass
class Archive:
    """Represents a parsed .3mf archive.

    Preserves all entries and their metadata so non-config entries
    can be written back byte-identical.
    """

    entries: list[ArchiveEntry] = field(default_factory=list)
    _entry_map: dict[str, int] = field(default_factory=dict, repr=False)

    def get_entry(self, path: str) -> ArchiveEntry | None:
        """Get an entry by its archive path."""
        idx = self._entry_map.get(path)
        if idx is None:
            return None
        return self.entries[idx]

    @property
    def config_entry(self) -> ArchiveEntry | None:
        """Get the project_settings.config entry."""
        return self.get_entry(CONFIG_PATH)

    @property
    def config_bytes(self) -> bytes:
        """Get raw bytes of project_settings.config."""
        entry = self.config_entry
        if entry is None:
            raise ValueError(f"Archive has no {CONFIG_PATH}")
        return entry.data

    @config_bytes.setter
    def config_bytes(self, value: bytes) -> None:
        """Replace the config bytes (for fixer pipeline)."""
        entry = self.config_entry
        if entry is None:
            raise ValueError(f"Archive has no {CONFIG_PATH}")
        entry.data = value

    def filament_config_paths(self) -> list[str]:
        """List paths that look like filament config entries."""
        return [
            e.info.filename
            for e in self.entries
            if e.info.filename.startswith("Metadata/")
            and e.info.filename.endswith(".config")
            and e.info.filename != CONFIG_PATH
        ]

    def get_filament_configs(self) -> dict[str, bytes]:
        """Get all filament config entries as path -> bytes."""
        result: dict[str, bytes] = {}
        for path in self.filament_config_paths():
            entry = self.get_entry(path)
            if entry is not None:
                result[path] = entry.data
        return result

    def set_filament_config(self, path: str, data: bytes) -> None:
        """Update a filament config entry."""
        entry = self.get_entry(path)
        if entry is None:
            raise ValueError(f"No entry at path: {path}")
        entry.data = data


def read_3mf(source: str | Path | BinaryIO) -> Archive:
    """Read a .3mf file and return an Archive preserving all entries.

    Args:
        source: Path to .3mf file or a file-like object.

    Returns:
        Archive with all entries indexed.
    """
    archive = Archive()

    if isinstance(source, (str, Path)):
        zf = zipfile.ZipFile(source, "r")
        should_close = True
    else:
        zf = zipfile.ZipFile(source, "r")
        should_close = True

    try:
        for info in zf.infolist():
            data = zf.read(info.filename)
            entry = ArchiveEntry(info=info, data=data)
            archive._entry_map[info.filename] = len(archive.entries)
            archive.entries.append(entry)
    finally:
        if should_close:
            zf.close()

    return archive


def write_3mf(archive: Archive, dest: str | Path | BinaryIO) -> None:
    """Write an Archive back to a .3mf file.

    Non-config entries are written with their original ZipInfo (preserving
    compression method, timestamps, etc.). Config entries that were modified
    get ZIP_DEFLATED compression.
    """
    if isinstance(dest, (str, Path)):
        zf = zipfile.ZipFile(dest, "w")
        should_close = True
    else:
        zf = zipfile.ZipFile(dest, "w")
        should_close = True

    try:
        for entry in archive.entries:
            # Use the original ZipInfo to preserve metadata.
            # For modified entries, the compress_type on the ZipInfo is kept
            # (the original method). If we want to force DEFLATED for rewritten
            # configs, we clone the ZipInfo.
            info = entry.info
            if _is_config_path(info.filename):
                # Clone the ZipInfo but force DEFLATED for config entries
                new_info = zipfile.ZipInfo(
                    filename=info.filename,
                    date_time=info.date_time,
                )
                new_info.compress_type = zipfile.ZIP_DEFLATED
                new_info.external_attr = info.external_attr
                zf.writestr(new_info, entry.data)
            else:
                # Passthrough: preserve original compression and metadata
                zf.writestr(info, entry.data)
    finally:
        if should_close:
            zf.close()


def _is_config_path(filename: str) -> bool:
    """Check if a path is a config file that we may rewrite."""
    return (
        filename == CONFIG_PATH
        or (filename.startswith("Metadata/") and filename.endswith(".config"))
    )
