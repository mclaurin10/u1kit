/**
 * End-to-end-ish integration test for the App shell.
 *
 * Simulates the full user journey — pick file, see lint results, toggle
 * a finding, choose a preset, click Apply, see the result, click Save-as
 * — without launching Tauri. Every Tauri API (shell Command, dialog
 * pickers, invoke) is mocked; the test asserts that each step produces
 * the expected state transition and that the right mock is called with
 * the right arguments.
 *
 * This is our equivalent of the Phase 3 plan's Playwright happy-path
 * spec — faster, more deterministic, and doesn't require a Linux CI
 * runner with a display server. Actual desktop-launch verification is
 * manual (documented in DECISIONS 39).
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import App from "./App";

// Mocks for every Tauri API the app uses.
const mockExecute = vi.fn();
const mockOpenDialog = vi.fn();
const mockSaveDialog = vi.fn();
const mockInvoke = vi.fn();

vi.mock("@tauri-apps/plugin-shell", () => ({
  Command: {
    create: vi.fn(() => ({ execute: mockExecute })),
  },
}));

vi.mock("@tauri-apps/api/path", () => ({
  resolveResource: vi.fn(async () => {
    throw new Error("no bundled resource in tests");
  }),
}));

vi.mock("@tauri-apps/plugin-dialog", () => ({
  open: (...args: unknown[]) => mockOpenDialog(...args),
  save: (...args: unknown[]) => mockSaveDialog(...args),
}));

vi.mock("@tauri-apps/api/core", () => ({
  invoke: (cmd: string, payload: unknown) => mockInvoke(cmd, payload),
}));

// Preset the CLI responses the app will see during the journey.
const PRESETS_PAYLOAD = {
  schema_version: "1",
  presets: [
    {
      name: "bambu-to-u1",
      description: "Convert Bambu → U1",
      source: "bundled",
    },
    { name: "peba-safe", description: "Flexible safe", source: "bundled" },
  ],
};

const LINT_PAYLOAD = {
  schema_version: "1",
  results: [
    {
      rule_id: "A2",
      severity: "fail",
      message: "Printer profile not U1",
      fixer_id: "a2",
      diff_preview: null,
    },
    {
      rule_id: "B3",
      severity: "warn",
      message: "Bambu-specific fields present",
      fixer_id: "b3",
      diff_preview: null,
    },
  ],
  fixers: null,
  summary: { fail: 1, warn: 1, info: 0 },
};

const FIX_PAYLOAD = {
  schema_version: "1",
  results: [],
  fixers: [
    { fixer_id: "a2", applied: true, message: "Applied" },
    { fixer_id: "b3", applied: true, message: "Applied" },
  ],
  summary: { fail: 0, warn: 0, info: 0 },
};

describe("App (integration)", () => {
  beforeEach(() => {
    mockExecute.mockReset();
    mockOpenDialog.mockReset();
    mockSaveDialog.mockReset();
    mockInvoke.mockReset();
  });

  it("walks the drop → lint → fix → save-as happy path", async () => {
    // 1) App boots and fetches presets.
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: JSON.stringify(PRESETS_PAYLOAD),
      stderr: "",
    });

    render(<App />);

    // Drop zone is the initial view.
    expect(
      await screen.findByRole("button", { name: /choose file/i }),
    ).toBeInTheDocument();

    // 2) User picks a file → lint fires.
    mockOpenDialog.mockResolvedValueOnce("C:/tmp/makerworld.3mf");
    mockExecute.mockResolvedValueOnce({
      code: 1, // exit 1 is expected when lint finds fail-severity findings
      stdout: JSON.stringify(LINT_PAYLOAD),
      stderr: "",
    });

    await userEvent.click(
      screen.getByRole("button", { name: /choose file/i }),
    );

    // 3) Findings render. The fail accordion is open by default
    // (DECISIONS G-iii) so A2 is visible; B3 is behind the closed warn
    // accordion, exercised separately in LintView unit tests.
    await waitFor(() => {
      expect(screen.getByTestId("finding-A2")).toBeInTheDocument();
    });
    expect(screen.getByText(/1 fail, 1 warn, 0 info/)).toBeInTheDocument();

    // 4) Apply fixes with the default bambu-to-u1 preset. Both fixable
    // findings are pre-checked by the reducer.
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: JSON.stringify(FIX_PAYLOAD),
      stderr: "",
    });
    await userEvent.click(screen.getByRole("button", { name: /apply/i }));

    // 5) FixResultView renders the applied fixers.
    await waitFor(() => {
      expect(screen.getByTestId("applied-a2")).toBeInTheDocument();
    });
    expect(screen.getByTestId("applied-b3")).toBeInTheDocument();

    // 6) Save-as flow: dialog returns a path, copy_file is invoked.
    mockSaveDialog.mockResolvedValueOnce("D:/saved/makerworld_u1.3mf");
    mockInvoke.mockResolvedValueOnce(undefined);

    await userEvent.click(screen.getByRole("button", { name: /save as/i }));

    await waitFor(() => {
      expect(mockInvoke).toHaveBeenCalledWith("copy_file", {
        src: "C:/tmp/makerworld_u1.3mf",
        dst: "D:/saved/makerworld_u1.3mf",
      });
    });
  });

  it("recovers gracefully when lint fails (CliCrashedError)", async () => {
    // Presets load fine.
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: JSON.stringify(PRESETS_PAYLOAD),
      stderr: "",
    });
    // User picks a file, but the sidecar crashes.
    mockOpenDialog.mockResolvedValueOnce("C:/tmp/broken.3mf");
    mockExecute.mockResolvedValueOnce({
      code: 2,
      stdout: "",
      stderr: "Traceback: missing project_settings.config",
    });

    render(<App />);
    await userEvent.click(
      await screen.findByRole("button", { name: /choose file/i }),
    );

    // Error card renders with a friendly message.
    await waitFor(() => {
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/exit 2/i)).toBeInTheDocument();

    // Try again works.
    await userEvent.click(
      screen.getByRole("button", { name: /try another file/i }),
    );
    expect(
      screen.getByRole("button", { name: /choose file/i }),
    ).toBeInTheDocument();
  });
});
