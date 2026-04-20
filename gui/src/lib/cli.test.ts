import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  CliCrashedError,
  CliMalformedJsonError,
  CliNotFoundError,
  CliSchemaMismatchError,
  runCli,
} from "./cli";

// Stub the Tauri APIs. `Command.create` returns a mocked object whose
// `execute()` resolves to whatever the test sets up. `resolveResource`
// always rejects so the wrapper falls through to the PATH path (what dev
// mode does anyway).
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

describe("runCli", () => {
  beforeEach(() => {
    mockExecute.mockReset();
  });

  it("returns the parsed payload on exit 0 with valid JSON", async () => {
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: '{"schema_version":"1","presets":[]}',
      stderr: "",
    });
    const data = await runCli(["presets", "list", "--json"]);
    expect(data).toEqual({ schema_version: "1", presets: [] });
  });

  it("returns the parsed payload on exit 1 (lint found fails — not an error)", async () => {
    mockExecute.mockResolvedValueOnce({
      code: 1,
      stdout:
        '{"schema_version":"1","results":[{"rule_id":"A2","severity":"fail","message":"x","fixer_id":"a2","diff_preview":null}],"fixers":null,"summary":{"fail":1,"warn":0,"info":0}}',
      stderr: "",
    });
    const data = await runCli(["lint", "x.3mf", "--json"]);
    expect(data.schema_version).toBe("1");
  });

  it("throws CliCrashedError on exit codes ≥2", async () => {
    mockExecute.mockResolvedValueOnce({
      code: 2,
      stdout: "",
      stderr: "boom",
    });
    await expect(runCli(["lint", "x.3mf"])).rejects.toBeInstanceOf(
      CliCrashedError,
    );
  });

  it("throws CliNotFoundError when Command.execute throws", async () => {
    mockExecute.mockRejectedValueOnce(new Error("command not found"));
    await expect(runCli(["--version"])).rejects.toBeInstanceOf(
      CliNotFoundError,
    );
  });

  it("throws CliMalformedJsonError on non-JSON stdout", async () => {
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: "hello, not json",
      stderr: "",
    });
    await expect(runCli(["--version"])).rejects.toBeInstanceOf(
      CliMalformedJsonError,
    );
  });

  it("throws CliSchemaMismatchError when schema_version !== '1'", async () => {
    mockExecute.mockResolvedValueOnce({
      code: 0,
      stdout: '{"schema_version":"2","presets":[]}',
      stderr: "",
    });
    await expect(runCli(["presets", "list", "--json"])).rejects.toBeInstanceOf(
      CliSchemaMismatchError,
    );
  });
});
