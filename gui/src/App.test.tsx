import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App (scaffold smoke)", () => {
  it("renders the product name", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "u1kit" })).toBeInTheDocument();
  });

  it("renders the verify-scaffold button", () => {
    render(<App />);
    expect(
      screen.getByRole("button", { name: /verify scaffold/i }),
    ).toBeInTheDocument();
  });
});
