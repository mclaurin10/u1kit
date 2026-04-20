/**
 * Class-component React error boundary. Catches render-time errors that
 * escape useEffect error handlers — for example, a component throwing
 * in render because it mis-handled a CLI response. The boundary shows a
 * "Something went wrong" card with the error message and a Reset action.
 *
 * React doesn't expose error boundaries via hooks, so this stays a class.
 */

import * as React from "react";

interface ErrorBoundaryState {
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  override state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  override componentDidCatch(error: Error, info: React.ErrorInfo): void {
    // Log to dev console; later tasks can wire a file-backed logger.
    // eslint-disable-next-line no-console
    console.error("ErrorBoundary caught:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ error: null });
  };

  override render() {
    if (this.state.error !== null) {
      return (
        <div className="container py-12">
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-6 text-sm">
            <p className="font-medium text-destructive">
              Something went wrong.
            </p>
            <p className="mt-1 text-muted-foreground">
              {this.state.error.message}
            </p>
            <button
              type="button"
              onClick={this.handleReset}
              className="mt-3 rounded-md border px-3 py-1 text-sm"
            >
              Reset
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
