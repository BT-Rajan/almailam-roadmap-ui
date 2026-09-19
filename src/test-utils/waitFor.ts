import { flushPromises } from '@vue/test-utils'

/** Polls `check` (flushing Vue/promise queues between tries) until it passes or the timeout elapses. */
export async function waitFor(check: () => boolean, timeoutMs = 3000, stepMs = 25): Promise<void> {
  const start = Date.now()
  while (Date.now() - start < timeoutMs) {
    await flushPromises()
    if (check()) return
    await new Promise((resolve) => setTimeout(resolve, stepMs))
  }
  throw new Error(`waitFor timed out after ${timeoutMs}ms`)
}

/** Lets pending timers/requests run for `ms` -- used to prove something has stopped happening. */
export async function settleFor(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms))
  await flushPromises()
}

/**
 * Resolves once `count()` has stopped changing for `quietMs`; throws if it is
 * still changing after `timeoutMs`. A page that finishes loading goes quiet;
 * one stuck in a reload/remount loop never does.
 */
export async function waitForQuiet(count: () => number, quietMs = 300, timeoutMs = 4000): Promise<void> {
  const start = Date.now()
  let last = count()
  let lastChange = Date.now()
  while (Date.now() - start < timeoutMs) {
    await settleFor(25)
    if (count() !== last) {
      last = count()
      lastChange = Date.now()
    } else if (Date.now() - lastChange >= quietMs) {
      return
    }
  }
  throw new Error(`still making requests after ${timeoutMs}ms (${count()} so far) -- a remount/reload loop?`)
}
