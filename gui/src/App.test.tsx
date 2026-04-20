import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import App from "./App";

describe("App", () => {
  it("renders the product heading and starts in the drop-zone view", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "u1kit" })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /choose file/i }),
    ).toBeInTheDocument();
  });
});
