import * as React from "react";
import { save as saveDialog } from "@tauri-apps/plugin-dialog";

import { DropZone } from "@/components/DropZone";
import { FixActionBar } from "@/components/FixActionBar";
import { FixResultView } from "@/components/FixResultView";
import { LintView } from "@/components/LintView";
import { RuleDocSheet } from "@/components/RuleDocSheet";
import { Button } from "@/components/ui/button";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { copyFile, fixFile, lintFile, listPresets } from "@/lib/cli";
import { initialSession, sessionReducer } from "@/state/session";

function defaultOutputName(sourcePath: string): string {
  // DECISIONS G-vi: `{stem}_u1.3mf`. Works with both / and \ separators.
  const lastSep = Math.max(
    sourcePath.lastIndexOf("/"),
    sourcePath.lastIndexOf("\\"),
  );
  const filename = lastSep === -1 ? sourcePath : sourcePath.slice(lastSep + 1);
  const dot = filename.lastIndexOf(".");
  const stem = dot === -1 ? filename : filename.slice(0, dot);
  return `${stem}_u1.3mf`;
}

function parentDir(sourcePath: string): string {
  const lastSep = Math.max(
    sourcePath.lastIndexOf("/"),
    sourcePath.lastIndexOf("\\"),
  );
  return lastSep === -1 ? "" : sourcePath.slice(0, lastSep);
}

function AppShell(): React.JSX.Element {
  const [state, dispatch] = React.useReducer(sessionReducer, initialSession);
  const [openRuleDoc, setOpenRuleDoc] = React.useState<string | null>(null);
  const { toast } = useToast();

  // One-time preset fetch at startup.
  React.useEffect(() => {
    let cancelled = false;
    async function run() {
      try {
        const presets = await listPresets();
        if (!cancelled) {
          dispatch({ type: "PRESETS_LOADED", presets });
        }
      } catch (cause) {
        if (cancelled) return;
        const message = cause instanceof Error ? cause.message : String(cause);
        toast(`Could not load presets: ${message}`, "destructive");
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [toast]);

  // Lint on FILE_DROPPED.
  React.useEffect(() => {
    if (state.status !== "fileLoaded" || state.filePath === null) return;
    let cancelled = false;
    const filePath = state.filePath;

    async function run() {
      dispatch({ type: "LINT_STARTED" });
      try {
        const lint = await lintFile(filePath);
        if (!cancelled) {
          dispatch({ type: "LINT_SUCCEEDED", lint });
        }
      } catch (cause) {
        if (cancelled) return;
        const message = cause instanceof Error ? cause.message : String(cause);
        dispatch({ type: "LINT_FAILED", error: message });
      }
    }
    void run();
    return () => {
      cancelled = true;
    };
  }, [state.status, state.filePath]);

  const handleApply = React.useCallback(async () => {
    if (state.filePath === null) return;
    if (state.checkedFixerIds.size === 0) return;

    dispatch({ type: "FIX_STARTED" });
    try {
      // Default output path: append `_u1` before `.3mf`. G8 replaces this
      // placeholder with a tempfile; Save-as copies to the user's choice.
      const outputPath = state.filePath.replace(/\.3mf$/i, "_u1.3mf");
      const fix = await fixFile(
        state.filePath,
        state.presetName,
        outputPath,
        [...state.checkedFixerIds],
      );
      dispatch({ type: "FIX_SUCCEEDED", fix });
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      dispatch({ type: "FIX_FAILED", error: message });
    }
  }, [state.filePath, state.presetName, state.checkedFixerIds]);

  return (
    <div className="container flex min-h-screen flex-col gap-6 py-8">
      <header className="flex items-baseline justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">u1kit</h1>
        {state.filePath !== null && state.status !== "fixing" && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => dispatch({ type: "RESET" })}
          >
            Start over
          </Button>
        )}
      </header>

      <main className="flex flex-1 flex-col gap-4">
        {state.status === "idle" && (
          <DropZone
            onFileSelected={(filePath) =>
              dispatch({ type: "FILE_DROPPED", filePath })
            }
          />
        )}

        {(state.status === "fileLoaded" || state.status === "linting") && (
          <div className="flex items-center gap-3 rounded-lg border bg-card p-6 text-card-foreground">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm">
              Linting{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                {state.filePath}
              </code>
              …
            </p>
          </div>
        )}

        {state.status === "showingFindings" && state.lint !== null && (
          <>
            <div className="rounded-lg border bg-card p-4 text-sm text-card-foreground">
              Loaded{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                {state.filePath}
              </code>{" "}
              — {state.lint.summary.fail} fail, {state.lint.summary.warn} warn,{" "}
              {state.lint.summary.info} info
            </div>
            <LintView
              lint={state.lint}
              checkedFixerIds={state.checkedFixerIds}
              onFindingToggle={(fixerId) =>
                dispatch({ type: "FINDING_TOGGLED", fixerId })
              }
              onWhy={setOpenRuleDoc}
            />
            {state.presets !== null && (
              <FixActionBar
                presets={state.presets.presets}
                presetName={state.presetName}
                onPresetChange={(name) =>
                  dispatch({ type: "PRESET_CHANGED", presetName: name })
                }
                checkedCount={state.checkedFixerIds.size}
                onApply={handleApply}
              />
            )}
          </>
        )}

        {state.status === "fixing" && (
          <div className="flex items-center gap-3 rounded-lg border bg-card p-6 text-card-foreground">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            <p className="text-sm">
              Applying preset{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                {state.presetName}
              </code>
              …
            </p>
          </div>
        )}

        {state.status === "done" &&
          state.fix !== null &&
          state.filePath !== null && (
            <FixResultView
              fix={state.fix}
              sourcePath={state.filePath}
              onSaveAs={async () => {
                if (state.fix === null || state.filePath === null) return;
                const defaultPath =
                  parentDir(state.filePath) +
                  (parentDir(state.filePath) === "" ? "" : "/") +
                  defaultOutputName(state.filePath);
                try {
                  const chosen = await saveDialog({
                    defaultPath,
                    filters: [{ name: "3MF", extensions: ["3mf"] }],
                  });
                  if (typeof chosen !== "string" || chosen === "") return;
                  // The CLI wrote the fix output at sourcePath_u1.3mf
                  // (matches defaultOutputName logic in App's handleApply).
                  const fixedOutput = state.filePath.replace(
                    /\.3mf$/i,
                    "_u1.3mf",
                  );
                  await copyFile(fixedOutput, chosen);
                  toast(`Saved to ${chosen}`);
                } catch (cause) {
                  const message =
                    cause instanceof Error ? cause.message : String(cause);
                  toast(`Save failed: ${message}`, "destructive");
                }
              }}
              onReset={() => dispatch({ type: "RESET" })}
            />
          )}

        {state.status === "error" && (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-sm">
            <p className="font-medium text-destructive">Something went wrong.</p>
            <p className="mt-1 text-muted-foreground">{state.error}</p>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => dispatch({ type: "RESET" })}
            >
              Try another file
            </Button>
          </div>
        )}
      </main>

      <RuleDocSheet
        ruleId={openRuleDoc}
        onOpenChange={(open) => !open && setOpenRuleDoc(null)}
      />
    </div>
  );
}

function App(): React.JSX.Element {
  return (
    <ToastProvider>
      <AppShell />
    </ToastProvider>
  );
}

export default App;
