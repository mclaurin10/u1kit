/**
 * Expandable finding row.
 *
 * - Collapsed: severity badge, rule id, one-line summary.
 * - Expanded: full message, diff preview (if present), Include-in-fix
 *   checkbox (disabled for findings with null fixer_id — informational
 *   rules), and a "Why?" button that opens the rule doc sheet.
 */

import * as React from "react";
import { ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";
import type { Finding, Severity } from "@/types/cli";

const SEVERITY_VARIANT: Record<Severity, "destructive" | "default" | "secondary"> =
  {
    fail: "destructive",
    warn: "default",
    info: "secondary",
  };

export interface FindingRowProps {
  finding: Finding;
  /** Whether this finding's fixer is checked for inclusion in the fix run. */
  checked: boolean;
  /** Called when the user toggles the checkbox. No-op if fixer_id is null. */
  onCheckedChange: (checked: boolean) => void;
  /** Called when the user clicks the "Why?" link. */
  onWhy: (ruleId: string) => void;
}

export function FindingRow({
  finding,
  checked,
  onCheckedChange,
  onWhy,
}: FindingRowProps) {
  const [expanded, setExpanded] = React.useState(false);
  const hasFixer = finding.fixer_id !== null;

  return (
    <div
      className="rounded-md border bg-card text-card-foreground"
      data-testid={`finding-${finding.rule_id}`}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 p-3 text-left"
        aria-expanded={expanded}
      >
        <ChevronRight
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform",
            expanded && "rotate-90",
          )}
          aria-hidden
        />
        <Badge variant={SEVERITY_VARIANT[finding.severity]}>
          {finding.severity}
        </Badge>
        <code className="text-xs font-semibold">{finding.rule_id}</code>
        <p className="flex-1 truncate text-sm">{finding.message}</p>
      </button>

      {expanded && (
        <div className="border-t px-3 pb-3 pt-2">
          <p className="whitespace-pre-wrap text-sm">{finding.message}</p>

          {finding.diff_preview !== null && (
            <pre className="mt-2 overflow-x-auto rounded bg-muted p-2 text-xs">
              <code>{finding.diff_preview}</code>
            </pre>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={checked}
                disabled={!hasFixer}
                onCheckedChange={(value) =>
                  onCheckedChange(value === true)
                }
                aria-label={`Include ${finding.rule_id} in fix`}
              />
              <span
                className={cn(
                  !hasFixer && "text-muted-foreground",
                )}
              >
                {hasFixer
                  ? "Include in fix"
                  : "Informational — no auto-fix"}
              </span>
            </label>
            <Button
              variant="link"
              size="sm"
              onClick={() => onWhy(finding.rule_id)}
            >
              Why?
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
