/**
 * Preset dropdown. Presets are grouped by source per DECISIONS G0-38:
 * bundled presets first, then user presets (if any) separated by a label.
 */

import * as React from "react";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PresetEntry } from "@/types/cli";

export interface PresetPickerProps {
  presets: PresetEntry[];
  value: string;
  onChange: (name: string) => void;
}

export function PresetPicker({
  presets,
  value,
  onChange,
}: PresetPickerProps): React.JSX.Element {
  const bundled = presets.filter((p) => p.source === "bundled");
  const user = presets.filter((p) => p.source === "user");

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[260px]" aria-label="Preset">
        <SelectValue placeholder="Pick a preset…" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Bundled</SelectLabel>
          {bundled.map((p) => (
            <SelectItem key={p.name} value={p.name}>
              {p.name}
            </SelectItem>
          ))}
        </SelectGroup>
        {user.length > 0 && (
          <>
            <SelectSeparator />
            <SelectGroup>
              <SelectLabel>User</SelectLabel>
              {user.map((p) => (
                <SelectItem key={p.name} value={p.name}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectGroup>
          </>
        )}
      </SelectContent>
    </Select>
  );
}
