/**
 * Side sheet showing the bundled markdown doc for a single rule. Rendered
 * via react-markdown; no network fetch. Closes via the built-in X button
 * or Esc key (inherited from Radix Dialog primitive).
 */

import ReactMarkdown from "react-markdown";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { getRuleDoc } from "@/lib/ruledocs";

export interface RuleDocSheetProps {
  ruleId: string | null;
  onOpenChange: (open: boolean) => void;
}

export function RuleDocSheet({ ruleId, onOpenChange }: RuleDocSheetProps) {
  const open = ruleId !== null;
  const doc = ruleId !== null ? getRuleDoc(ruleId) : null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto">
        <SheetHeader>
          <SheetTitle>{ruleId ?? "Rule doc"}</SheetTitle>
          <SheetDescription>
            {doc === null
              ? "No documentation bundled for this rule."
              : "Bundled rule reference — why this rule exists and what the fixer does."}
          </SheetDescription>
        </SheetHeader>
        {doc !== null && (
          <article className="prose prose-sm mt-4 max-w-none dark:prose-invert">
            <ReactMarkdown>{doc}</ReactMarkdown>
          </article>
        )}
      </SheetContent>
    </Sheet>
  );
}
