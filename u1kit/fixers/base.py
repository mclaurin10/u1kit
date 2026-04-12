"""Fixer base class and pipeline orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from u1kit.rules.base import Context, Result, Rule


class FixMode(Enum):
    """How the pipeline should apply fixes."""

    DRY_RUN = "dry-run"
    AUTO = "auto"
    INTERACTIVE = "interactive"


class FixerAbort(Exception):  # noqa: N818
    """Signals that a fixer refused to apply and the pipeline should record
    a skipped FixerResult instead of crashing.

    Subclasses carry domain-specific meaning (e.g. B1MergeRequiresConsent).
    """


@dataclass
class FixerResult:
    """Outcome of applying a fixer."""

    fixer_id: str
    applied: bool
    message: str


class Fixer(ABC):
    """Abstract base for all fixers."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Fixer ID, matching the fixer_id in rule Results."""
        ...

    @abstractmethod
    def apply(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        context: Context,
    ) -> None:
        """Apply the fix in-place to config and/or filament_configs."""
        ...


class Pipeline:
    """Runs rules, collects results, optionally applies fixers."""

    def __init__(
        self,
        rules: list[type[Rule]],
        fixers: dict[str, Fixer],
        mode: FixMode = FixMode.AUTO,
        interactive_callback: Callable[[Result, Fixer], bool] | None = None,
    ) -> None:
        self.rules = rules
        self.fixers = fixers
        self.mode = mode
        self.interactive_callback = interactive_callback

    def run_rules(self, context: Context) -> list[Result]:
        """Run all rules and return results."""
        results: list[Result] = []
        for rule_cls in self.rules:
            rule = rule_cls()
            results.extend(rule.check(context))
        return results

    def run(
        self,
        config: dict[str, Any],
        filament_configs: dict[str, dict[str, Any]],
        options: dict[str, Any] | None = None,
    ) -> tuple[list[Result], list[FixerResult], dict[str, Any], dict[str, dict[str, Any]]]:
        """Run the full pipeline: lint then fix.

        Returns:
            Tuple of (rule_results, fixer_results, updated_config, updated_filament_configs).
        """
        context = Context(
            config=config,
            filament_configs=filament_configs,
            options=options or {},
        )

        # Run rules
        results = self.run_rules(context)

        if self.mode == FixMode.DRY_RUN:
            return results, [], config, filament_configs

        # Collect fixable results
        fixer_results: list[FixerResult] = []
        fixable = [r for r in results if r.fixer_id is not None]

        # Deduplicate by fixer_id (multiple results may point to same fixer)
        seen_fixers: set[str] = set()
        for result in fixable:
            fixer_id = result.fixer_id
            assert fixer_id is not None
            if fixer_id in seen_fixers:
                continue

            fixer = self.fixers.get(fixer_id)
            if fixer is None:
                fixer_results.append(
                    FixerResult(
                        fixer_id=fixer_id,
                        applied=False,
                        message=f"No fixer registered for {fixer_id!r}",
                    )
                )
                seen_fixers.add(fixer_id)
                continue

            should_apply = True
            if self.mode == FixMode.INTERACTIVE and self.interactive_callback:
                should_apply = self.interactive_callback(result, fixer)

            if should_apply:
                try:
                    fixer.apply(config, filament_configs, context)
                except FixerAbort as exc:
                    fixer_results.append(
                        FixerResult(
                            fixer_id=fixer_id,
                            applied=False,
                            message=str(exc),
                        )
                    )
                    seen_fixers.add(fixer_id)
                    continue
                fixer_results.append(
                    FixerResult(fixer_id=fixer_id, applied=True, message="Applied")
                )
            else:
                fixer_results.append(
                    FixerResult(fixer_id=fixer_id, applied=False, message="Skipped by user")
                )

            seen_fixers.add(fixer_id)

        return results, fixer_results, config, filament_configs
