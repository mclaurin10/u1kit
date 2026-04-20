/**
 * Top-level app state machine, per DECISIONS item 33 (useReducer, no Redux).
 *
 * The session walks through Idle → FileLoaded → Linting → ShowingFindings →
 * Fixing → Done. Error can be entered from Linting or Fixing on CLI failure;
 * RESET snaps back to Idle from any state.
 *
 * The reducer is intentionally small — additional UI concerns (which
 * accordion is open, which finding is selected) are local state in the
 * relevant component. Things that must survive a state transition
 * (filePath through the whole flow, preset selection into the fix)
 * belong here.
 */

import type {
  FixResponse,
  LintResponse,
  PresetsListResponse,
} from "@/types/cli";

export type SessionStatus =
  | "idle"
  | "fileLoaded"
  | "linting"
  | "showingFindings"
  | "fixing"
  | "done"
  | "error";

export interface SessionState {
  status: SessionStatus;
  /** Absolute path of the .3mf picked by the user, once chosen. */
  filePath: string | null;
  /** Discovered presets, fetched once at startup. */
  presets: PresetsListResponse | null;
  /** Name of the preset the user picked; defaults to `bambu-to-u1`. */
  presetName: string;
  /** Lint response (when status is ShowingFindings / Fixing / Done). */
  lint: LintResponse | null;
  /** Fix response (when status is Done). */
  fix: FixResponse | null;
  /** Fixer IDs the user has checked for inclusion in the fix run. */
  checkedFixerIds: Set<string>;
  /** User-visible error message. Cleared on RESET. */
  error: string | null;
}

export const initialSession: SessionState = {
  status: "idle",
  filePath: null,
  presets: null,
  presetName: "bambu-to-u1",
  lint: null,
  fix: null,
  checkedFixerIds: new Set(),
  error: null,
};

export type SessionAction =
  | { type: "PRESETS_LOADED"; presets: PresetsListResponse }
  | { type: "FILE_DROPPED"; filePath: string }
  | { type: "FILE_CLEARED" }
  | { type: "LINT_STARTED" }
  | { type: "LINT_SUCCEEDED"; lint: LintResponse }
  | { type: "LINT_FAILED"; error: string }
  | { type: "PRESET_CHANGED"; presetName: string }
  | { type: "FINDING_TOGGLED"; fixerId: string }
  | { type: "FIX_STARTED" }
  | { type: "FIX_SUCCEEDED"; fix: FixResponse }
  | { type: "FIX_FAILED"; error: string }
  | { type: "RESET" };

export function sessionReducer(
  state: SessionState,
  action: SessionAction,
): SessionState {
  switch (action.type) {
    case "PRESETS_LOADED":
      return { ...state, presets: action.presets };

    case "FILE_DROPPED":
      return {
        ...state,
        status: "fileLoaded",
        filePath: action.filePath,
        lint: null,
        fix: null,
        checkedFixerIds: new Set(),
        error: null,
      };

    case "FILE_CLEARED":
      return {
        ...state,
        status: "idle",
        filePath: null,
        lint: null,
        fix: null,
        checkedFixerIds: new Set(),
        error: null,
      };

    case "LINT_STARTED":
      return { ...state, status: "linting", error: null };

    case "LINT_SUCCEEDED": {
      // Check every fixable finding by default (DECISIONS item G-v).
      const checked = new Set(
        action.lint.results
          .map((r) => r.fixer_id)
          .filter((id): id is string => id !== null),
      );
      return {
        ...state,
        status: "showingFindings",
        lint: action.lint,
        checkedFixerIds: checked,
      };
    }

    case "LINT_FAILED":
      return { ...state, status: "error", error: action.error };

    case "PRESET_CHANGED":
      return { ...state, presetName: action.presetName };

    case "FINDING_TOGGLED": {
      const next = new Set(state.checkedFixerIds);
      if (next.has(action.fixerId)) {
        next.delete(action.fixerId);
      } else {
        next.add(action.fixerId);
      }
      return { ...state, checkedFixerIds: next };
    }

    case "FIX_STARTED":
      return { ...state, status: "fixing", error: null };

    case "FIX_SUCCEEDED":
      return { ...state, status: "done", fix: action.fix };

    case "FIX_FAILED":
      return { ...state, status: "error", error: action.error };

    case "RESET":
      return initialSession;

    default:
      // Exhaustiveness check — `action satisfies never` makes TypeScript
      // error if a new action type is added without a case above.
      return assertNever(action);
  }
}

function assertNever(value: never): never {
  throw new Error(`Unhandled session action: ${JSON.stringify(value)}`);
}
