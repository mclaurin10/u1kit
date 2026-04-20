/**
 * Minimal toast implementation — not the full shadcn Sonner/Radix toast,
 * just enough for the drop-zone rejection path (G4) and a handful of
 * other short-lived notifications. Can be swapped for a richer library
 * later without changing the `toast()` call sites.
 */

import * as React from "react";
import { cn } from "@/lib/utils";

interface ToastMessage {
  id: number;
  text: string;
  variant: "default" | "destructive";
}

type ToastContextValue = {
  toast: (text: string, variant?: ToastMessage["variant"]) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

let nextId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<ToastMessage[]>([]);

  const toast = React.useCallback<ToastContextValue["toast"]>(
    (text, variant = "default") => {
      const id = ++nextId;
      setToasts((prev) => [...prev, { id, text, variant }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 3500);
    },
    [],
  );

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div
        role="region"
        aria-label="Notifications"
        className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2"
      >
        {toasts.map((t) => (
          <div
            key={t.id}
            role="status"
            className={cn(
              "pointer-events-auto rounded-md border px-4 py-3 text-sm shadow-md",
              t.variant === "destructive"
                ? "border-destructive/50 bg-destructive text-destructive-foreground"
                : "border-border bg-card text-card-foreground",
            )}
          >
            {t.text}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = React.useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }
  return ctx;
}
