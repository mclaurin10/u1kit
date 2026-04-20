/**
 * Synchronous rule-doc map built from `gui/src/ruledocs/*.md` at build time.
 *
 * Vite's `import.meta.glob` with `{ as: "raw", eager: true }` inlines the
 * markdown source into the bundle — no network fetch, no runtime I/O.
 * This means rule docs ship with the app and cannot drift from the
 * version of u1kit that shipped alongside them.
 */

// The `?raw` query imports the file contents as a string; `eager: true`
// resolves synchronously at build time so the map is a plain object.
const raw = import.meta.glob<string>("../ruledocs/*.md", {
  query: "?raw",
  import: "default",
  eager: true,
});

function filenameToRuleId(path: string): string {
  const match = path.match(/([^/]+)\.md$/);
  if (!match || !match[1]) {
    throw new Error(`Unexpected ruledocs path: ${path}`);
  }
  return match[1].toUpperCase();
}

const RULE_DOCS: Record<string, string> = Object.fromEntries(
  Object.entries(raw).map(([path, contents]) => [
    filenameToRuleId(path),
    contents,
  ]),
);

/**
 * Return the markdown source for a rule, or null if no doc exists.
 * Callers can render the result with `react-markdown`.
 */
export function getRuleDoc(ruleId: string): string | null {
  return RULE_DOCS[ruleId.toUpperCase()] ?? null;
}

export function listDocumentedRules(): string[] {
  return Object.keys(RULE_DOCS).sort();
}
