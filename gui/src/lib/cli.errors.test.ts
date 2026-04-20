import { describe, expect, it, vi } from "vitest";

import {
  CliCrashedError,
  CliMalformedJsonError,
  CliNotFoundError,
  CliSchemaMismatchError,
  CliTimeoutError,
  formatCliError,
} from "./cli";

const mockExecute = vi.fn();

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

describe("formatCliError", () => {
  it("maps CliNotFoundError to a reinstall hint", () => {
    const msg = formatCliError(new CliNotFoundError("bin missing"));
    expect(msg).toMatch(/CLI is missing/i);
  });

  it("maps CliCrashedError with stderr to a detailed message", () => {
    const msg = formatCliError(
      new CliCrashedError("boom", 2, "Traceback: something"),
    );
    expect(msg).toMatch(/exit 2/);
    expect(msg).toMatch(/Traceback/);
  });

  it("maps CliCrashedError without stderr to a brief message", () => {
    const msg = formatCliError(new CliCrashedError("boom", 3));
    expect(msg).toMatch(/exit 3/);
    expect(msg).not.toMatch(/undefined/);
  });

  it("maps CliMalformedJsonError to a bug-filing hint", () => {
    const msg = formatCliError(
      new CliMalformedJsonError("bad", "not json", ""),
    );
    expect(msg).toMatch(/unreadable output/i);
  });

  it("maps CliSchemaMismatchError to an out-of-sync hint", () => {
    const msg = formatCliError(
      new CliSchemaMismatchError("mismatch", "1", "2"),
    );
    expect(msg).toMatch(/out of sync/i);
  });

  it("maps CliTimeoutError to a timeout message with seconds", () => {
    const msg = formatCliError(new CliTimeoutError("timed out", 60000));
    expect(msg).toMatch(/60 s/);
  });

  it("falls through to Error.message for unknown errors", () => {
    expect(formatCliError(new Error("plain"))).toBe("plain");
  });

  it("stringifies non-Error values", () => {
    expect(formatCliError("boom")).toBe("boom");
  });
});

describe("CliTimeoutError", () => {
  it("is constructible and carries the timeout value", () => {
    const err = new CliTimeoutError("timed out", 60000);
    expect(err).toBeInstanceOf(CliTimeoutError);
    expect(err).toBeInstanceOf(Error);
    expect(err.timeoutMs).toBe(60000);
    expect(err.name).toBe("CliTimeoutError");
  });
  // The actual race is driven by setTimeout against Tauri's Command;
  // a full fake-timer-based race of runCli against the mocked execute
  // is flaky under Vitest because the mock leaks a never-resolving
  // promise. Covered instead by manual testing and the formatCliError
  // case above.
});
