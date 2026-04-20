import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FindingRow } from "./FindingRow";
import type { Finding } from "@/types/cli";

function fail(fixerId: string | null = "a2"): Finding {
  return {
    rule_id: "A2",
    severity: "fail",
    message: "printer profile not U1",
    fixer_id: fixerId,
    diff_preview: "- Bambu Lab X1 Carbon\n+ Snapmaker U1",
  };
}

describe("FindingRow", () => {
  it("renders the severity badge, rule id, and message truncated", () => {
    render(
      <FindingRow
        finding={fail()}
        checked={true}
        onCheckedChange={() => {}}
        onWhy={() => {}}
      />,
    );
    expect(screen.getByText("A2")).toBeInTheDocument();
    expect(screen.getByText(/printer profile not U1/)).toBeInTheDocument();
  });

  it("expands when the header is clicked, showing diff + checkbox", async () => {
    render(
      <FindingRow
        finding={fail()}
        checked={true}
        onCheckedChange={() => {}}
        onWhy={() => {}}
      />,
    );
    // Diff preview is hidden until expanded.
    expect(screen.queryByText(/Bambu Lab X1 Carbon/)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button"));
    expect(screen.getByText(/Bambu Lab X1 Carbon/)).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: /include A2 in fix/i }),
    ).toBeInTheDocument();
  });

  it("disables the checkbox for findings with null fixer_id", async () => {
    render(
      <FindingRow
        finding={{
          rule_id: "A1",
          severity: "info",
          message: "source",
          fixer_id: null,
          diff_preview: null,
        }}
        checked={false}
        onCheckedChange={() => {}}
        onWhy={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button"));
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeDisabled();
  });

  it("calls onCheckedChange when the checkbox is toggled", async () => {
    const onCheckedChange = vi.fn();
    render(
      <FindingRow
        finding={fail()}
        checked={false}
        onCheckedChange={onCheckedChange}
        onWhy={() => {}}
      />,
    );
    await userEvent.click(screen.getByRole("button"));
    await userEvent.click(screen.getByRole("checkbox"));
    expect(onCheckedChange).toHaveBeenCalledWith(true);
  });

  it("calls onWhy with the rule id when the 'Why?' link is clicked", async () => {
    const onWhy = vi.fn();
    render(
      <FindingRow
        finding={fail()}
        checked={true}
        onCheckedChange={() => {}}
        onWhy={onWhy}
      />,
    );
    await userEvent.click(screen.getByRole("button"));
    await userEvent.click(screen.getByRole("button", { name: /why/i }));
    expect(onWhy).toHaveBeenCalledWith("A2");
  });
});
