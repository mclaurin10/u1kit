import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { RuleDocSheet } from "./RuleDocSheet";

describe("RuleDocSheet", () => {
  it("renders nothing (closed) when ruleId is null", () => {
    render(<RuleDocSheet ruleId={null} onOpenChange={() => {}} />);
    // Sheet renders its content only when open, which requires ruleId.
    expect(screen.queryByText(/A2 — Printer/)).not.toBeInTheDocument();
  });

  it("renders the bundled doc when ruleId is a known rule", () => {
    render(<RuleDocSheet ruleId="A2" onOpenChange={() => {}} />);
    expect(screen.getByText(/Printer profile not U1/)).toBeInTheDocument();
  });

  it("shows a fallback message for unknown rule ids", () => {
    render(<RuleDocSheet ruleId="ZZ" onOpenChange={() => {}} />);
    expect(
      screen.getByText(/No documentation bundled/i),
    ).toBeInTheDocument();
  });
});
