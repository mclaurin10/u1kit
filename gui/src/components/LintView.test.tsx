import { describe, expect, it } from "vitest";
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

describe("LintView", () => {
  it("shows 'No issues' when results is empty", () => {
    render(<LintView lint={lint([])} />);
    expect(screen.getByText(/no issues found/i)).toBeInTheDocument();
  });

  it("renders three severity groups with counts", () => {
    render(
      <LintView
        lint={lint([
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
        ])}
      />,
    );

    expect(screen.getByText(/Failing/)).toBeInTheDocument();
    expect(screen.getByText(/Warnings/)).toBeInTheDocument();
    expect(screen.getByText(/Info/)).toBeInTheDocument();
    // Counts render next to the labels.
    expect(screen.getAllByText(/\(1\)/).length).toBeGreaterThanOrEqual(3);
  });

  it("opens the Failing group by default when it has findings", () => {
    render(
      <LintView
        lint={lint([
          {
            rule_id: "A2",
            severity: "fail",
            message: "profile",
            fixer_id: "a2",
            diff_preview: null,
          },
        ])}
      />,
    );
    // The fail-severity finding's row is visible because the group is open.
    expect(screen.getByTestId("finding-A2")).toBeInTheDocument();
  });

  it("opens the first non-empty group when no fails (e.g. warn)", () => {
    render(
      <LintView
        lint={lint([
          {
            rule_id: "B3",
            severity: "warn",
            message: "bbl fields",
            fixer_id: "b3",
            diff_preview: null,
          },
        ])}
      />,
    );
    expect(screen.getByTestId("finding-B3")).toBeInTheDocument();
  });
});
