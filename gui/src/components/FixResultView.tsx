/**
 * Shown after the fix CLI invocation completes successfully. Lists
 * applied/skipped fixers and surfaces the output path. A Save-as button
 * (wired in G8) lets the user copy the output to a location of their
 * choice.
 */

import * as React from "react";
import { Check, Minus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { FixResponse } from "@/types/cli";

export interface FixResultViewProps {
  fix: FixResponse;
  sourcePath: string;
  onSaveAs?: () => void;
  onReset: () => void;
}

export function FixResultView({
  fix,
  onSaveAs,
  onReset,
}: FixResultViewProps): React.JSX.Element {
  const applied = fix.fixers.filter((f) => f.applied);
  const skipped = fix.fixers.filter((f) => !f.applied);

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border bg-card p-4 text-card-foreground">
        <h2 className="text-base font-semibold">Fix complete</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          {applied.length} fixer{applied.length === 1 ? "" : "s"} applied
          {skipped.length > 0 && `, ${skipped.length} skipped`}.
        </p>
      </div>

      {applied.length > 0 && (
        <section className="rounded-lg border bg-card p-4 text-card-foreground">
          <h3 className="mb-2 text-sm font-medium">Applied</h3>
          <ul className="flex flex-col gap-1">
            {applied.map((f) => (
              <li
                key={f.fixer_id}
                className="flex items-center gap-2 text-sm"
                data-testid={`applied-${f.fixer_id}`}
              >
                <Check className="h-4 w-4 text-green-600" aria-hidden />
                <code className="text-xs font-semibold">{f.fixer_id}</code>
                <span className="text-muted-foreground">{f.message}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {skipped.length > 0 && (
        <section className="rounded-lg border bg-card p-4 text-card-foreground">
          <h3 className="mb-2 text-sm font-medium">Skipped</h3>
          <ul className="flex flex-col gap-1">
            {skipped.map((f) => (
              <li
                key={f.fixer_id}
                className="flex items-center gap-2 text-sm"
                data-testid={`skipped-${f.fixer_id}`}
              >
                <Minus className="h-4 w-4 text-muted-foreground" aria-hidden />
                <code className="text-xs font-semibold">{f.fixer_id}</code>
                <Badge variant="outline">{f.message}</Badge>
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="flex items-center gap-3">
        {onSaveAs !== undefined && (
          <Button onClick={onSaveAs}>Save as…</Button>
        )}
        <Button variant="outline" onClick={onReset}>
          Fix another file
        </Button>
      </div>
    </div>
  );
}
