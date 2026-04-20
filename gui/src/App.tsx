import * as React from "react";

import { DropZone } from "@/components/DropZone";
import { LintView } from "@/components/LintView";
import { RuleDocSheet } from "@/components/RuleDocSheet";
import { Button } from "@/components/ui/button";
import { ToastProvider } from "@/components/ui/toast";
import { lintFile } from "@/lib/cli";
import { initialSession, sessionReducer } from "@/state/session";

function AppShell(): React.JSX.Element {
  const [state, dispatch] = React.useReducer(sessionReducer, initialSession);
  const [openRuleDoc, setOpenRuleDoc] = React.useState<string | null>(null);

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

  return (
    <div className="container flex min-h-screen flex-col gap-6 py-8">
      <header className="flex items-baseline justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">u1kit</h1>
        {state.filePath !== null && (
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
          </>
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
