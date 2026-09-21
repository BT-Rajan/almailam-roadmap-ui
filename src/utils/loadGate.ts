/**
 * Coordinates repeated loads of the same data so pages that all "ensure X is
 * loaded" don't each trigger their own full download.
 *
 * - Concurrent callers share ONE in-flight request instead of racing several.
 * - A successful load stays "fresh" for `ttlMs`; a non-forced call inside that
 *   window returns immediately without touching the network.
 * - `force: true` always issues a new request. Use it wherever correctness
 *   depends on seeing changes made elsewhere since the last load (e.g. the
 *   New Project wizard's eligible-client list). A forced load never joins an
 *   older in-flight request, since that request may have started before the
 *   change the caller is trying to observe.
 * - Only the most recently *started* load counts as "current". The `load`
 *   callback receives `isCurrent()` so it can skip applying a stale response
 *   that finished after a newer request had already been issued.
 *
 * `load` must resolve `true` on success and `false` on a handled failure (a
 * failed load does not mark the data fresh, so the next call retries). It may
 * also reject; the rejection reaches the caller and the gate resets cleanly.
 */
export interface LoadGate {
  run(load: (isCurrent: () => boolean) => Promise<boolean>, options?: { force?: boolean }): Promise<void>
  /** Marks the data stale so the next non-forced `run` refetches. */
  invalidate(): void
}

export function createLoadGate(ttlMs: number, now: () => number = Date.now): LoadGate {
  let generation = 0
  let loadedAt: number | null = null
  let inFlight: Promise<void> | null = null

  return {
    run(load, options = {}) {
      if (!options.force) {
        if (inFlight) return inFlight
        if (loadedAt !== null && now() - loadedAt < ttlMs) return Promise.resolve()
      }

      const myGeneration = ++generation
      const isCurrent = () => myGeneration === generation

      const promise: Promise<void> = load(isCurrent)
        .then((succeeded) => {
          if (succeeded && isCurrent()) loadedAt = now()
        })
        .finally(() => {
          if (inFlight === promise) inFlight = null
        })
      inFlight = promise
      return promise
    },

    invalidate() {
      loadedAt = null
    },
  }
}

// One gate per (store instance, key). Keyed on the store instance rather than
// held at module level so a fresh Pinia (a new test, or a re-created app)
// always starts with a clean gate instead of inheriting another instance's
// freshness window.
const gatesByOwner = new WeakMap<object, Map<string, LoadGate>>()

export function getLoadGate(owner: object, key: string, ttlMs: number): LoadGate {
  let gates = gatesByOwner.get(owner)
  if (!gates) {
    gates = new Map()
    gatesByOwner.set(owner, gates)
  }
  let gate = gates.get(key)
  if (!gate) {
    gate = createLoadGate(ttlMs)
    gates.set(key, gate)
  }
  return gate
}

/**
 * How long a successful load counts as fresh for callers that just need the
 * data present (e.g. a dialog resolving names, or a tab re-opened moments
 * later). Short on purpose: other users' changes show up within this window,
 * and anything that must see a change made moments ago passes `force: true`.
 */
export const CACHE_TTL_MS = 30_000
