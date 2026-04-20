import { describe, expect, it } from "vitest";

import { initialSession, sessionReducer } from "./session";
import type { Finding, LintResponse } from "@/types/cli";

function makeLintResponse(results: Finding[]): LintResponse {
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

describe("sessionReducer", () => {
  it("starts idle with null file and no error", () => {
    expect(initialSession.status).toBe("idle");
    expect(initialSession.filePath).toBeNull();
    expect(initialSession.error).toBeNull();
  });

  it("FILE_DROPPED transitions to fileLoaded with the path set", () => {
    const next = sessionReducer(initialSession, {
      type: "FILE_DROPPED",
      filePath: "/tmp/x.3mf",
    });
    expect(next.status).toBe("fileLoaded");
    expect(next.filePath).toBe("/tmp/x.3mf");
  });

  it("LINT_SUCCEEDED pre-checks every fixable finding by default", () => {
    const lint = makeLintResponse([
      {
        rule_id: "A2",
        severity: "fail",
        message: "…",
        fixer_id: "a2",
        diff_preview: null,
      },
      {
        rule_id: "A1",
        severity: "info",
        message: "…",
        fixer_id: null, // informational — not checkable
        diff_preview: null,
      },
      {
        rule_id: "B3",
        severity: "warn",
        message: "…",
        fixer_id: "b3",
        diff_preview: null,
      },
    ]);

    const next = sessionReducer(
      { ...initialSession, status: "linting" },
      { type: "LINT_SUCCEEDED", lint },
    );

    expect(next.status).toBe("showingFindings");
    expect(next.checkedFixerIds).toEqual(new Set(["a2", "b3"]));
  });

  it("FINDING_TOGGLED adds then removes a fixer_id", () => {
    const afterAdd = sessionReducer(initialSession, {
      type: "FINDING_TOGGLED",
      fixerId: "a2",
    });
    expect(afterAdd.checkedFixerIds.has("a2")).toBe(true);

    const afterRemove = sessionReducer(afterAdd, {
      type: "FINDING_TOGGLED",
      fixerId: "a2",
    });
    expect(afterRemove.checkedFixerIds.has("a2")).toBe(false);
  });

  it("LINT_FAILED moves to error with the message", () => {
    const next = sessionReducer(initialSession, {
      type: "LINT_FAILED",
      error: "boom",
    });
    expect(next.status).toBe("error");
    expect(next.error).toBe("boom");
  });

  it("RESET restores initial state", () => {
    const mid = sessionReducer(initialSession, {
      type: "FILE_DROPPED",
      filePath: "/tmp/x.3mf",
    });
    const reset = sessionReducer(mid, { type: "RESET" });
    expect(reset).toEqual(initialSession);
  });

  it("PRESET_CHANGED updates presetName without touching other state", () => {
    const mid = sessionReducer(initialSession, {
      type: "FILE_DROPPED",
      filePath: "/tmp/x.3mf",
    });
    const next = sessionReducer(mid, {
      type: "PRESET_CHANGED",
      presetName: "peba-safe",
    });
    expect(next.presetName).toBe("peba-safe");
    expect(next.filePath).toBe("/tmp/x.3mf");
    expect(next.status).toBe("fileLoaded");
  });
});
