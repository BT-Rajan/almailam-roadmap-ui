/**
 * Replaces one scope's rows inside a larger shared list, leaving every other
 * row untouched. Used when a store loads just one project's records: the
 * fresh rows swap in for that project's old ones, and rows already loaded for
 * other projects stay where they are.
 *
 * Returns a new array (never mutates `existing`) so Pinia/Vue see the change.
 */
export function replaceScope<T>(existing: T[], fresh: T[], inScope: (item: T) => boolean): T[] {
  return [...existing.filter((item) => !inScope(item)), ...fresh]
}
