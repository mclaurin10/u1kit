import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DropZone } from "./DropZone";
import { ToastProvider } from "@/components/ui/toast";

const mockOpen = vi.fn();

vi.mock("@tauri-apps/plugin-dialog", () => ({
  open: (...args: unknown[]) => mockOpen(...args),
}));

function renderDropZone(onFileSelected = vi.fn()) {
  return {
    onFileSelected,
    ...render(
      <ToastProvider>
        <DropZone onFileSelected={onFileSelected} />
      </ToastProvider>,
    ),
  };
}

describe("DropZone", () => {
  beforeEach(() => {
    mockOpen.mockReset();
  });

  it("renders a drop-zone and a browse button", () => {
    renderDropZone();
    expect(screen.getByTestId("drop-zone")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /choose file/i }),
    ).toBeInTheDocument();
  });

  it("click on browse opens the picker and reports the selected path", async () => {
    mockOpen.mockResolvedValueOnce("C:/tmp/test.3mf");
    const { onFileSelected } = renderDropZone();

    await userEvent.click(
      screen.getByRole("button", { name: /choose file/i }),
    );

    expect(mockOpen).toHaveBeenCalled();
    expect(onFileSelected).toHaveBeenCalledWith("C:/tmp/test.3mf");
  });

  it("ignores picker cancellation (null return) silently", async () => {
    mockOpen.mockResolvedValueOnce(null);
    const { onFileSelected } = renderDropZone();

    await userEvent.click(
      screen.getByRole("button", { name: /choose file/i }),
    );
    expect(onFileSelected).not.toHaveBeenCalled();
  });

  it("rejects a non-3mf/zip extension with a toast", async () => {
    mockOpen.mockResolvedValueOnce("C:/tmp/test.pdf");
    const { onFileSelected } = renderDropZone();

    await userEvent.click(
      screen.getByRole("button", { name: /choose file/i }),
    );

    expect(onFileSelected).not.toHaveBeenCalled();
    // The toast shows up in the DOM.
    expect(
      await screen.findByText(/only .3mf and .zip files are supported/i),
    ).toBeInTheDocument();
  });
});
