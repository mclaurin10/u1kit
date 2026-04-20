import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ErrorBoundary } from "./ErrorBoundary";

function Thrower(): React.JSX.Element {
  throw new Error("kaboom");
}

describe("ErrorBoundary", () => {
  // The boundary logs to console.error; silence it during these tests to
  // keep output readable. Spy + restore.
  let consoleSpy: ReturnType<typeof vi.spyOn>;

  beforeAll(() => {
    consoleSpy = vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterAll(() => {
    consoleSpy.mockRestore();
  });

  it("renders its children when there is no error", () => {
    render(
      <ErrorBoundary>
        <span>safe</span>
      </ErrorBoundary>,
    );
    expect(screen.getByText("safe")).toBeInTheDocument();
  });

  it("catches a thrown error and renders a fallback with the message", () => {
    render(
      <ErrorBoundary>
        <Thrower />
      </ErrorBoundary>,
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByText(/kaboom/)).toBeInTheDocument();
  });

  it("Reset button is rendered and clickable after an error", async () => {
    render(
      <ErrorBoundary>
        <Thrower />
      </ErrorBoundary>,
    );
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();

    const resetButton = screen.getByRole("button", { name: /reset/i });
    expect(resetButton).toBeInTheDocument();
    // Clicking the reset button calls setState; recovery requires the
    // parent to swap in non-throwing children, which is a real-app
    // concern (App's RESET action) not a boundary concern.
    await userEvent.click(resetButton);
  });
});
