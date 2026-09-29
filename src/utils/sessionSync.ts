// Cross-tab session coordination.
//
// Every open tab shares one httpOnly refresh cookie, but each tab used to
// run its own idle timer, its own refresh and its own logout with no idea
// the others existed. That is what signed people out "at random":
//
//   - a tab left idle in the background hit its 30-minute idle timeout and
//     called logout(), which revokes the shared refresh token server-side,
//     so the tab the person was actually working in was thrown out on its
//     next token refresh;
//   - two tabs refreshing at the same moment both sent the same single-use
//     refresh token, and whichever arrived second was rejected as revoked.
//
// This module gives the tabs a shared view: activity in any tab counts as
// activity for all of them, refreshes are serialized across tabs, and a
// real logout in one tab is announced to the others.
//
// Every storage/channel access is wrapped: private windows, blocked site
// data and older browsers must degrade to the old per-tab behaviour, never
// throw.

const ACTIVITY_KEY = 'serviceos:lastActivity'
const CHANNEL_NAME = 'serviceos-auth'
const REFRESH_LOCK_NAME = 'serviceos-auth-refresh'
// mousemove/scroll fire constantly; one write every few seconds is plenty
// for a 30-minute timeout.
const ACTIVITY_WRITE_INTERVAL_MS = 5_000

let lastActivityWrite = 0

/** Records that the person did something in this tab, visible to every tab. */
export function recordActivity(now: number = Date.now()): void {
  if (now - lastActivityWrite < ACTIVITY_WRITE_INTERVAL_MS) return
  lastActivityWrite = now
  try {
    localStorage.setItem(ACTIVITY_KEY, String(now))
  } catch {
    // Storage unavailable: idle tracking falls back to this tab alone.
  }
}

/** Most recent activity recorded by any tab, or 0 if unknown. */
export function lastSharedActivity(): number {
  try {
    const value = Number(localStorage.getItem(ACTIVITY_KEY))
    return Number.isFinite(value) ? value : 0
  } catch {
    return 0
  }
}

/**
 * Runs `fn` while holding a lock shared by every tab of this origin, so only
 * one tab at a time redeems the single-use refresh cookie. A tab that waited
 * sends whatever cookie the previous holder left behind (the browser reads
 * the cookie jar when the request is sent), so it refreshes successfully
 * instead of replaying a token that was just rotated away.
 */
export async function withRefreshLock<T>(fn: () => Promise<T>): Promise<T> {
  const locks = typeof navigator !== 'undefined' ? navigator.locks : undefined
  if (!locks) return fn()
  return locks.request(REFRESH_LOCK_NAME, fn) as Promise<T>
}

type LogoutListener = () => void

function openChannel(): BroadcastChannel | null {
  try {
    return typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel(CHANNEL_NAME)
  } catch {
    return null
  }
}

/** Tells every other tab that this session has ended. */
export function broadcastLogout(): void {
  const channel = openChannel()
  if (!channel) return
  try {
    channel.postMessage({ type: 'logout' })
  } finally {
    channel.close()
  }
}

/** Calls `listener` when another tab ends the session. Returns an unsubscribe function. */
export function onRemoteLogout(listener: LogoutListener): () => void {
  const channel = openChannel()
  if (!channel) return () => {}
  channel.onmessage = (event: MessageEvent) => {
    if (event.data?.type === 'logout') listener()
  }
  return () => channel.close()
}
