import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FixResultView } from "./FixResultView";
import type { FixResponse } from "@/types/cli";

function fix(): FixResponse {
  return {
    schema_version: "1",
    results: [],
    fixers: [
      { fixer_id: "a2", applied: true, message: "Applied" },
      { fixer_id: "b3", applied: true, message: "Applied" },
      {
        fixer_id: "e3",
        applied: false,
        message: "E3 brim bump requires opt-in",
      },
    ],
    summary: { fail: 0, warn: 0, info: 0 },
  };
}

describe("FixResultView", () => {
  it("lists applied and skipped fixers separately", () => {
    render(
      <FixResultView
        fix={fix()}
        sourcePath="/tmp/x.3mf"
        onReset={() => {}}
      />,
    );
    expect(screen.getByTestId("applied-a2")).toBeInTheDocument();
    expect(screen.getByTestId("applied-b3")).toBeInTheDocument();
    expect(screen.getByTestId("skipped-e3")).toBeInTheDocument();
  });

  it("shows a Save-as button only when onSaveAs is provided", () => {
    const { rerender } = render(
      <FixResultView
        fix={fix()}
        sourcePath="/tmp/x.3mf"
        onReset={() => {}}
      />,
    );
    expect(
      screen.queryByRole("button", { name: /save as/i }),
    ).not.toBeInTheDocument();

    rerender(
      <FixResultView
        fix={fix()}
        sourcePath="/tmp/x.3mf"
        onSaveAs={() => {}}
        onReset={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /save as/i })).toBeInTheDocument();
  });

  it("calls onReset when the Fix-another button is clicked", async () => {
    const onReset = vi.fn();
    render(
      <FixResultView
        fix={fix()}
        sourcePath="/tmp/x.3mf"
        onReset={onReset}
      />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: /fix another/i }),
    );
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});
