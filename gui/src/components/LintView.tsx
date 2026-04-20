/**
 * Lint view: findings grouped by severity into three accordions.
 * DECISIONS G-iii — groups are ordered fail → warn → info; the first
 * non-empty group is open by default.
 */

import * as React from "react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { FindingRow } from "@/components/FindingRow";
import type { Finding, LintResponse, Severity } from "@/types/cli";

const GROUP_ORDER: Severity[] = ["fail", "warn", "info"];

const GROUP_LABEL: Record<Severity, string> = {
  fail: "Failing",
  warn: "Warnings",
  info: "Info",
};

function groupBySeverity(findings: Finding[]): Record<Severity, Finding[]> {
  const groups: Record<Severity, Finding[]> = { fail: [], warn: [], info: [] };
  for (const f of findings) {
    groups[f.severity].push(f);
  }
  return groups;
}

function pickDefaultOpen(groups: Record<Severity, Finding[]>): string[] {
  for (const sev of GROUP_ORDER) {
    if (groups[sev].length > 0) {
      return [sev];
    }
  }
  return [];
}

export interface LintViewProps {
  lint: LintResponse;
}

export function LintView({ lint }: LintViewProps): React.JSX.Element {
  const groups = React.useMemo(
    () => groupBySeverity(lint.results),
    [lint.results],
  );
  const defaultOpen = React.useMemo(() => pickDefaultOpen(groups), [groups]);

  if (lint.results.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-6 text-card-foreground">
        <p className="text-sm">No issues found.</p>
      </div>
    );
  }

  return (
    <Accordion
      type="multiple"
      defaultValue={defaultOpen}
      className="rounded-lg border bg-card text-card-foreground"
    >
      {GROUP_ORDER.map((sev) => (
        <AccordionItem key={sev} value={sev}>
          <AccordionTrigger className="px-4">
            <span>
              {GROUP_LABEL[sev]}{" "}
              <span className="text-muted-foreground">
                ({groups[sev].length})
              </span>
            </span>
          </AccordionTrigger>
          <AccordionContent className="px-4">
            {groups[sev].length === 0 ? (
              <p className="text-sm text-muted-foreground">None.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {groups[sev].map((f) => (
                  <FindingRow key={`${f.rule_id}-${f.message}`} finding={f} />
                ))}
              </div>
            )}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}
