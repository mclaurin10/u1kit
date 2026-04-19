"""Base types for the rule system."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from u1kit.geometry import ObjectBounds


class Severity(Enum):
    """Rule result severity levels."""

    FAIL = "fail"
    WARN = "warn"
    INFO = "info"


@dataclass
class Result:
    """The outcome of a single rule check."""

    rule_id: str
    severity: Severity
    message: str
    fixer_id: str | None = None
    diff_preview: str | None = None


@dataclass
class Context:
    """All the data a rule needs to make its check.

    Attributes:
        config: Parsed project_settings.config dict.
        filament_configs: Mapping of archive path -> parsed filament config dict.
        source_slicer: Detected source slicer (set by A1 for downstream rules).
        options: CLI options like uniform_height.
    """

    config: dict[str, Any]
    filament_configs: dict[str, dict[str, Any]] = field(default_factory=dict)
    source_slicer: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    geometry_bounds: list[ObjectBounds] | None = None


class Rule(ABC):
    """Abstract base for all rules."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable rule ID (e.g. 'A1'). Public API — never rename."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable rule name."""
        ...

    @abstractmethod
    def check(self, context: Context) -> list[Result]:
        """Run the rule check and return zero or more results."""
        ...
