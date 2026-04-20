import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { FixActionBar } from "./FixActionBar";
import type { PresetEntry } from "@/types/cli";

const PRESETS: PresetEntry[] = [
  {
    name: "bambu-to-u1",
    description: "",
    source: "bundled",
  },
  {
    name: "peba-safe",
    description: "",
    source: "bundled",
  },
];

describe("FixActionBar", () => {
  it("renders the preset value and checked count", () => {
    render(
      <FixActionBar
        presets={PRESETS}
        presetName="bambu-to-u1"
        onPresetChange={() => {}}
        checkedCount={3}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText(/bambu-to-u1/)).toBeInTheDocument();
    expect(screen.getByText(/3 fixers selected/i)).toBeInTheDocument();
  });

  it("disables Apply when no fixers are checked", () => {
    render(
      <FixActionBar
        presets={PRESETS}
        presetName="bambu-to-u1"
        onPresetChange={() => {}}
        checkedCount={0}
        onApply={() => {}}
      />,
    );
    expect(screen.getByRole("button", { name: /apply/i })).toBeDisabled();
  });

  it("fires onApply when clicked", async () => {
    const onApply = vi.fn();
    render(
      <FixActionBar
        presets={PRESETS}
        presetName="bambu-to-u1"
        onPresetChange={() => {}}
        checkedCount={1}
        onApply={onApply}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /apply/i }));
    expect(onApply).toHaveBeenCalledTimes(1);
  });
});
