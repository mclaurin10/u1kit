import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

import { LintView } from "./LintView";
import type { Finding, LintResponse } from "@/types/cli";

function lint(results: Finding[]): LintResponse {
  return {
    schema_version: "1",
    results,
    fixers: null,
    summary: {
      fail: results.filter((r) => r.severity === "fail").length,
      warn: results.filter((r) => r.severity === "warn").length,
      info: results.filter((r) => r.severity === "info").length,
    },
  };
}

function renderLint(results: Finding[], checkedFixerIds = new Set<string>()) {
  const onFindingToggle = vi.fn();
  const onWhy = vi.fn();
  return {
    onFindingToggle,
    onWhy,
    ...render(
      <LintView
        lint={lint(results)}
        checkedFixerIds={checkedFixerIds}
        onFindingToggle={onFindingToggle}
        onWhy={onWhy}
      />,
    ),
  };
}

describe("LintView", () => {
  it("shows 'No issues' when results is empty", () => {
    renderLint([]);
    expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
  });

  it("renders three severity groups with counts", () => {
    renderLint([
      {
        rule_id: "A2",
        severity: "fail",
        message: "profile",
        fixer_id: "a2",
        diff_preview: null,
      },
      {
        rule_id: "B3",
        severity: "warn",
        message: "bbl fields",
        fixer_id: "b3",
        diff_preview: null,
      },
      {
        rule_id: "A1",
        severity: "info",
        message: "source",
        fixer_id: null,
        diff_preview: null,
      },
    ]);

    expect(screen.getByText(/Failing/)).toBeInTheDocument();
    expect(screen.getByText(/Warnings/)).toBeInTheDocument();
    expect(screen.getByText(/Info/)).toBeInTheDocument();
    expect(screen.getAllByText(/\(1\)/).length).toBeGreaterThanOrEqual(3);
  });

  it("opens the Failing group by default when it has findings", () => {
    renderLint([
      {
        rule_id: "A2",
        severity: "fail",
        message: "profile",
        fixer_id: "a2",
        diff_preview: null,
      },
    ]);
    expect(screen.getByTestId("finding-A2")).toBeInTheDocument();
  });

  it("opens the first non-empty group when no fails (e.g. warn)", () => {
    renderLint([
      {
        rule_id: "B3",
        severity: "warn",
        message: "bbl fields",
        fixer_id: "b3",
        diff_preview: null,
      },
    ]);
    expect(screen.getByTestId("finding-B3")).toBeInTheDocument();
  });
});
