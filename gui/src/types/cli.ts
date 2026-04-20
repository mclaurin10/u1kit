/**
 * TypeScript mirrors of the u1kit CLI's JSON contracts.
 *
 * These shapes are emitted by `u1kit/report.py` (lint/fix) and
 * `u1kit/cli.py::presets_list` (presets list). The CLI's
 * `schema_version: "1"` promise means these interfaces are stable
 * across patch/minor releases; any breaking change requires a bump
 * to schema_version "2" and a deliberate GUI update.
 *
 * **Do not reshape these without updating the CLI in the same
 * commit.** Drift between the CLI's emitted JSON and these interfaces
 * is exactly the class of bug `runCli<T>()` (below) is designed to
 * catch early via runtime validation.
 */

export type Severity = "fail" | "warn" | "info";

export interface Finding {
  rule_id: string;
  severity: Severity;
  message: string;
  fixer_id: string | null;
  diff_preview: string | null;
}

export interface LintSummary {
  fail: number;
  warn: number;
  info: number;
}

export interface LintResponse {
  schema_version: "1";
  results: Finding[];
  /** `null` when the response comes from the plain `lint` command. */
  fixers: FixerOutcome[] | null;
  summary: LintSummary;
}

export interface FixerOutcome {
  fixer_id: string;
  /** `true` if the fixer actually ran; `false` if it was skipped or aborted. */
  applied: boolean;
  message: string;
}

export interface FixResponse {
  schema_version: "1";
  results: Finding[];
  fixers: FixerOutcome[];
  summary: LintSummary;
}

export interface PresetEntry {
  name: string;
  description: string;
  source: "bundled" | "user";
}

export interface PresetsListResponse {
  schema_version: "1";
  presets: PresetEntry[];
}
