/**
 * Typed wrapper around `u1kit` CLI invocations via Tauri's shell plugin.
 *
 * All interactions with the CLI flow through `runCli<T>()`, which:
 * 1. Resolves the sidecar binary path (dev = system PATH; prod = bundled).
 * 2. Captures stdout and parses it as JSON.
 * 3. Validates `schema_version === "1"` before returning — any drift
 *    from the documented shape raises a typed error rather than
 *    silently returning malformed data.
 *
 * Exit code semantics (matches the CLI):
 *   0 — clean / operation succeeded
 *   1 — operation succeeded but lint found fail-severity findings
 *        (still returns the parsed payload; not an error)
 *   2+ — crash / internal error (throws `CliCrashedError`)
 */

import { Command } from "@tauri-apps/plugin-shell";
import { resolveResource } from "@tauri-apps/api/path";
import { invoke } from "@tauri-apps/api/core";

import type {
  FixResponse,
  LintResponse,
  PresetsListResponse,
} from "@/types/cli";

/**
 * Base class for all CLI-layer errors. Discriminated by `.name` so a
 * React ErrorBoundary can match on type.
 */
export class CliError extends Error {
  override name = "CliError";
  constructor(message: string, public readonly stderr?: string) {
    super(message);
  }
}

export class CliNotFoundError extends CliError {
  override name = "CliNotFoundError";
}

export class CliCrashedError extends CliError {
  override name = "CliCrashedError";
  constructor(
    message: string,
    public readonly exitCode: number,
    stderr?: string,
  ) {
    super(message, stderr);
  }
}

export class CliMalformedJsonError extends CliError {
  override name = "CliMalformedJsonError";
  constructor(
    message: string,
    public readonly stdout: string,
    stderr?: string,
  ) {
    super(message, stderr);
  }
}

export class CliSchemaMismatchError extends CliError {
  override name = "CliSchemaMismatchError";
  constructor(
    message: string,
    public readonly expected: string,
    public readonly actual: unknown,
  ) {
    super(message);
  }
}

export class CliTimeoutError extends CliError {
  override name = "CliTimeoutError";
  constructor(message: string, public readonly timeoutMs: number) {
    super(message);
  }
}

/** Hard cap per sidecar call — 60 s is generous for even worst-case lint/fix. */
const CLI_TIMEOUT_MS = 60_000;

/** Race a promise against a timeout. Throws CliTimeoutError on overrun. */
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new CliTimeoutError(`Timed out after ${ms}ms`, ms));
    }, ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (err) => {
        clearTimeout(timer);
        reject(err instanceof Error ? err : new Error(String(err)));
      },
    );
  });
}

/**
 * Map a thrown error to a user-facing message. Unknown errors fall
 * through as-is; every typed CliError becomes a short, actionable line.
 */
export function formatCliError(cause: unknown): string {
  if (cause instanceof CliNotFoundError) {
    return "u1kit CLI is missing. Reinstall or check your PATH.";
  }
  if (cause instanceof CliCrashedError) {
    const detail = cause.stderr?.trim();
    return detail
      ? `u1kit crashed (exit ${cause.exitCode}): ${detail}`
      : `u1kit crashed (exit ${cause.exitCode}).`;
  }
  if (cause instanceof CliMalformedJsonError) {
    return "u1kit returned unreadable output. This usually means a log line leaked into stdout — file a bug.";
  }
  if (cause instanceof CliSchemaMismatchError) {
    return `u1kit JSON schema mismatch (expected ${cause.expected}, got ${String(cause.actual)}). The GUI and CLI are out of sync — reinstall both.`;
  }
  if (cause instanceof CliTimeoutError) {
    return `u1kit took longer than ${Math.round(cause.timeoutMs / 1000)} s and was aborted.`;
  }
  if (cause instanceof Error) {
    return cause.message;
  }
  return String(cause);
}

/**
 * Resolve the sidecar binary path. In dev, we rely on `u1kit` being on
 * PATH. In a Tauri release build, the binary ships inside the app bundle
 * under `resources/sidecar/<target-triple>/u1kit`. We try the bundled
 * path first and fall back to the PATH lookup — this lets the GUI work
 * during `tauri dev` without packaging the sidecar every change.
 */
async function resolveSidecarCommand(args: string[]): Promise<Command<string>> {
  try {
    const bundled = await resolveResource("resources/sidecar/u1kit");
    return Command.create(bundled, args);
  } catch {
    // Fall through to PATH lookup (dev mode).
  }
  return Command.create("u1kit", args);
}

/**
 * Invoke the CLI and return the parsed, schema-validated JSON payload.
 *
 * Exit codes 0 and 1 are both treated as "command ran to completion";
 * 1 is expected for `lint` when there are fail-severity findings. Any
 * other non-zero code is a crash and throws `CliCrashedError`.
 */
export async function runCli<
  T extends { schema_version: "1" } = LintResponse | FixResponse | PresetsListResponse,
>(args: string[]): Promise<T> {
  let output;
  try {
    const cmd = await resolveSidecarCommand(args);
    output = await withTimeout(cmd.execute(), CLI_TIMEOUT_MS);
  } catch (cause) {
    if (cause instanceof CliTimeoutError) throw cause;
    const message = cause instanceof Error ? cause.message : String(cause);
    throw new CliNotFoundError(
      `Failed to invoke u1kit CLI: ${message}. ` +
        `Is u1kit on PATH (dev) or bundled in the app (prod)?`,
    );
  }

  if (output.code !== 0 && output.code !== 1) {
    throw new CliCrashedError(
      `u1kit exited with code ${output.code}`,
      output.code ?? -1,
      output.stderr,
    );
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(output.stdout);
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : String(cause);
    throw new CliMalformedJsonError(
      `u1kit stdout was not valid JSON: ${message}`,
      output.stdout,
      output.stderr,
    );
  }

  if (
    typeof parsed !== "object" ||
    parsed === null ||
    (parsed as { schema_version?: unknown }).schema_version !== "1"
  ) {
    throw new CliSchemaMismatchError(
      "u1kit JSON missing or mismatched schema_version",
      "1",
      (parsed as { schema_version?: unknown })?.schema_version,
    );
  }

  return parsed as T;
}

/**
 * Thin convenience wrappers. The GUI could call `runCli` directly, but
 * these make intent clearer at call sites and concentrate the argument
 * construction (e.g. `--json`) in one place.
 */
export async function lintFile(filePath: string): Promise<LintResponse> {
  return runCli<LintResponse>(["lint", filePath, "--json"]);
}

export async function fixFile(
  filePath: string,
  preset: string,
  outputPath: string,
  onlyFixerIds?: string[],
): Promise<FixResponse> {
  const args = [
    "fix",
    filePath,
    "--preset",
    preset,
    "--out",
    outputPath,
    "--json",
  ];
  if (onlyFixerIds !== undefined && onlyFixerIds.length > 0) {
    for (const id of onlyFixerIds) {
      args.push("--only", id);
    }
  }
  return runCli<FixResponse>(args);
}

export async function listPresets(): Promise<PresetsListResponse> {
  return runCli<PresetsListResponse>(["presets", "list", "--json"]);
}

/**
 * Copy `src` to `dst`. Used by the Save-as flow (G8) to copy the fix
 * command's output to the user-chosen destination. Overwrites `dst`
 * without prompting — Tauri's dialog.save() already asks for confirm.
 */
export async function copyFile(src: string, dst: string): Promise<void> {
  await invoke("copy_file", { src, dst });
}
