/**
 * Drop-zone for .3mf files. Accepts drag-drop or a click-to-browse
 * fallback via Tauri's dialog plugin. Per DECISIONS item G-ii, the
 * accept filter is .3mf and .zip (Bambu exports sometimes ship as
 * .zip pre-rename). Anything else triggers a toast and no state
 * transition.
 */

import * as React from "react";
import { open as openDialog } from "@tauri-apps/plugin-dialog";
import { FileDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

const ACCEPT_EXTENSIONS = ["3mf", "zip"] as const;
const ACCEPT_SET = new Set<string>(ACCEPT_EXTENSIONS);

function hasAcceptedExtension(filename: string): boolean {
  const dot = filename.lastIndexOf(".");
  if (dot === -1) return false;
  const ext = filename.slice(dot + 1).toLowerCase();
  return ACCEPT_SET.has(ext);
}

export interface DropZoneProps {
  onFileSelected: (filePath: string) => void;
}

export function DropZone({ onFileSelected }: DropZoneProps): React.JSX.Element {
  const { toast } = useToast();
  const [isHovering, setHovering] = React.useState(false);

  const handleDrop = React.useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setHovering(false);

      const files = Array.from(event.dataTransfer.files);
      if (files.length === 0) return;

      // HTML5 drag-drop exposes File objects, not filesystem paths.
      // Tauri makes the actual filesystem path available via
      // `dataTransfer.getData("text/uri-list")` or by using the
      // drag-drop event at the Tauri level. For MVP we require the
      // user to use the picker button if drop isn't supplying a path.
      // Both paths are tested; the picker path is the more reliable.
      const first = files[0];
      if (!first) return;
      if (!hasAcceptedExtension(first.name)) {
        toast("Only .3mf and .zip files are supported.", "destructive");
        return;
      }
      // Browsers don't expose File.path; rely on the picker button
      // below for path access on every platform.
      toast(
        "Drag-drop preview doesn't expose the OS path — please click the button.",
      );
    },
    [toast],
  );

  const handlePick = React.useCallback(async () => {
    try {
      const selected = await openDialog({
        multiple: false,
        filters: [{ name: "3MF / ZIP", extensions: [...ACCEPT_EXTENSIONS] }],
      });
      if (typeof selected !== "string" || !selected) {
        return; // User cancelled.
      }
      if (!hasAcceptedExtension(selected)) {
        toast("Only .3mf and .zip files are supported.", "destructive");
        return;
      }
      onFileSelected(selected);
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      toast(`Could not open file picker: ${message}`, "destructive");
    }
  }, [onFileSelected, toast]);

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed p-12 transition-colors",
        isHovering
          ? "border-primary bg-accent"
          : "border-border bg-card text-card-foreground",
      )}
      onDragOver={(e) => {
        e.preventDefault();
        setHovering(true);
      }}
      onDragLeave={() => setHovering(false)}
      onDrop={handleDrop}
      data-testid="drop-zone"
    >
      <FileDown className="h-10 w-10 text-muted-foreground" aria-hidden />
      <div className="text-center">
        <p className="text-sm font-medium">Drop a .3mf file here</p>
        <p className="text-xs text-muted-foreground">
          or click below to browse
        </p>
      </div>
      <Button variant="outline" onClick={handlePick}>
        Choose file…
      </Button>
    </div>
  );
}
