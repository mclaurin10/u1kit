import * as React from "react";

import { DropZone } from "@/components/DropZone";
import { Button } from "@/components/ui/button";
import { ToastProvider } from "@/components/ui/toast";
import { initialSession, sessionReducer } from "@/state/session";

/**
 * Top-level app shell. Owns the session reducer; renders a view based
 * on `state.status`. Subsequent tasks expand the view cases:
 *   - G5: Linting / ShowingFindings lint view
 *   - G7: Fixing / Done with apply workflow
 *   - G9: Error with typed messaging
 */
function AppShell(): React.JSX.Element {
  const [state, dispatch] = React.useReducer(sessionReducer, initialSession);

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

        {state.status === "fileLoaded" && state.filePath !== null && (
          <div className="rounded-lg border bg-card p-6 text-card-foreground">
            <p className="text-sm">
              Loaded{" "}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                {state.filePath}
              </code>
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Lint view (G5) replaces this placeholder next.
            </p>
          </div>
        )}
      </main>
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
