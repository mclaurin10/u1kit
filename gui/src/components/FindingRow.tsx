/**
 * Minimal finding row — rule id, severity badge, message. G6 expands
 * this with a collapsible detail, diff preview, and "Why?" link to the
 * bundled rule doc.
 */

import { Badge } from "@/components/ui/badge";
import type { Finding, Severity } from "@/types/cli";

const SEVERITY_VARIANT: Record<Severity, "destructive" | "default" | "secondary"> =
  {
    fail: "destructive",
    warn: "default",
    info: "secondary",
  };

const SEVERITY_LABEL: Record<Severity, string> = {
  fail: "fail",
  warn: "warn",
  info: "info",
};

export interface FindingRowProps {
  finding: Finding;
}

export function FindingRow({ finding }: FindingRowProps) {
  return (
    <div
      className="flex flex-col gap-1 rounded-md border bg-card p-3 text-card-foreground"
      data-testid={`finding-${finding.rule_id}`}
    >
      <div className="flex items-center gap-2">
        <Badge variant={SEVERITY_VARIANT[finding.severity]}>
          {SEVERITY_LABEL[finding.severity]}
        </Badge>
        <code className="text-xs font-semibold">{finding.rule_id}</code>
      </div>
      <p className="whitespace-pre-wrap text-sm">{finding.message}</p>
    </div>
  );
}
