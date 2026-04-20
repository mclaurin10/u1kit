/**
 * Sticky bottom action bar shown on the ShowingFindings state. Contains
 * the preset picker, a checked-count summary, and the primary "Apply
 * fixes" button.
 */

import * as React from "react";

import { PresetPicker } from "@/components/PresetPicker";
import { Button } from "@/components/ui/button";
import type { PresetEntry } from "@/types/cli";

export interface FixActionBarProps {
  presets: PresetEntry[];
  presetName: string;
  onPresetChange: (name: string) => void;
  checkedCount: number;
  disabled?: boolean;
  onApply: () => void;
}

export function FixActionBar({
  presets,
  presetName,
  onPresetChange,
  checkedCount,
  disabled,
  onApply,
}: FixActionBarProps): React.JSX.Element {
  return (
    <div className="sticky bottom-0 flex items-center justify-between gap-4 rounded-lg border bg-card p-3 text-card-foreground shadow-sm">
      <div className="flex items-center gap-3">
        <PresetPicker
          presets={presets}
          value={presetName}
          onChange={onPresetChange}
        />
        <span className="text-sm text-muted-foreground">
          {checkedCount} {checkedCount === 1 ? "fixer" : "fixers"} selected
        </span>
      </div>
      <Button
        onClick={onApply}
        disabled={disabled === true || checkedCount === 0}
      >
        Apply fixes
      </Button>
    </div>
  );
}
