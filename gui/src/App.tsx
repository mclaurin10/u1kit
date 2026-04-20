import { Button } from "@/components/ui/button";

/**
 * Phase 3 scaffold — this file is a placeholder wired through the full stack
 * (Tauri + React + Vite + Tailwind + shadcn). Subsequent tasks replace it
 * with the drop-zone (G4), lint view (G5), etc.
 */
function App() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background text-foreground">
      <h1 className="text-4xl font-semibold tracking-tight">u1kit</h1>
      <p className="max-w-md text-center text-muted-foreground">
        Convert Bambu/Makerworld .3mf files for the Snapmaker U1. Drop a file
        to start — support for that drop zone lands in G4.
      </p>
      <Button onClick={() => console.log("Hello from u1kit")}>
        Verify scaffold
      </Button>
    </div>
  );
}

export default App;
