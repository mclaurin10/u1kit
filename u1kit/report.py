"""JSON and human-readable report formatters."""

from __future__ import annotations

import json
from typing import Any

from u1kit.fixers.base import FixerResult
from u1kit.rules.base import Result, Severity

SEVERITY_SYMBOLS = {
    Severity.FAIL: "FAIL",
    Severity.WARN: "WARN",
    Severity.INFO: "INFO",
}

SEVERITY_COLORS = {
    Severity.FAIL: "\033[31m",  # red
    Severity.WARN: "\033[33m",  # yellow
    Severity.INFO: "\033[36m",  # cyan
}

RESET = "\033[0m"


def format_human(
    results: list[Result],
    fixer_results: list[FixerResult] | None = None,
    use_color: bool = True,
) -> str:
    """Format results as human-readable text.

    Args:
        results: Rule check results.
        fixer_results: Optional fixer application results.
        use_color: Whether to include ANSI color codes.

    Returns:
        Formatted string.
    """
    lines: list[str] = []

    if not results:
        lines.append("No issues found.")
        return "\n".join(lines)

    for result in results:
        sym = SEVERITY_SYMBOLS[result.severity]
        if use_color:
            color = SEVERITY_COLORS[result.severity]
            prefix = f"{color}[{sym}]{RESET}"
        else:
            prefix = f"[{sym}]"

        lines.append(f"{prefix} {result.rule_id}: {result.message}")
        if result.diff_preview:
            for diff_line in result.diff_preview.split("\n"):
                lines.append(f"      {diff_line}")

    if fixer_results:
        lines.append("")
        lines.append("Fixers:")
        for fr in fixer_results:
            status = "applied" if fr.applied else "skipped"
            lines.append(f"  {fr.fixer_id}: {status} - {fr.message}")

    # Summary
    fails = sum(1 for r in results if r.severity == Severity.FAIL)
    warns = sum(1 for r in results if r.severity == Severity.WARN)
    infos = sum(1 for r in results if r.severity == Severity.INFO)
    lines.append("")
    lines.append(f"Summary: {fails} fail, {warns} warn, {infos} info")

    return "\n".join(lines)


def format_json(
    results: list[Result],
    fixer_results: list[FixerResult] | None = None,
) -> str:
    """Format results as stable JSON.

    Schema:
    {
        "results": [{"rule_id": str, "severity": str, "message": str,
                     "fixer_id": str|null, "diff_preview": str|null}],
        "fixers": [{"fixer_id": str, "applied": bool, "message": str}] | null,
        "summary": {"fail": int, "warn": int, "info": int}
    }
    """
    data: dict[str, Any] = {
        "results": [
            {
                "rule_id": r.rule_id,
                "severity": r.severity.value,
                "message": r.message,
                "fixer_id": r.fixer_id,
                "diff_preview": r.diff_preview,
            }
            for r in results
        ],
        "fixers": (
            [
                {
                    "fixer_id": fr.fixer_id,
                    "applied": fr.applied,
                    "message": fr.message,
                }
                for fr in fixer_results
            ]
            if fixer_results is not None
            else None
        ),
        "summary": {
            "fail": sum(1 for r in results if r.severity == Severity.FAIL),
            "warn": sum(1 for r in results if r.severity == Severity.WARN),
            "info": sum(1 for r in results if r.severity == Severity.INFO),
        },
    }
    return json.dumps(data, indent=2)
