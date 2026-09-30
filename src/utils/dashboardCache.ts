// Last-seen Dashboard figures, kept in this browser so a tab can show
// them instantly while fresh ones load (see useDashboardData).
//
// Scoped to the signed-in user (a different person on the same browser
// never sees them), ignored once older than MAX_AGE_MS, and wiped whenever
// a session ends (authStore._clearToken) -- the Financials tab holds money
// figures, so nothing outlives the sign-in it was loaded under. Storage
// can be unavailable (private mode, blocked site data), so every access is
// best-effort.

const PREFIX = 'serviceos.dashboard.'
const VERSION = 1
const MAX_AGE_MS = 24 * 60 * 60 * 1000

interface Entry<T> {
  v: number
  userId: string
  savedAt: number
  data: T
}

function storage(): Storage | undefined {
  try {
    return window.localStorage
  } catch {
    return undefined
  }
}

export function readDashboardCache<T>(tab: string, userId: string | undefined): { data: T; savedAt: number } | undefined {
  if (!userId) return undefined
  try {
    const raw = storage()?.getItem(PREFIX + tab)
    if (!raw) return undefined
    const entry = JSON.parse(raw) as Entry<T>
    if (entry.v !== VERSION || entry.userId !== userId || Date.now() - entry.savedAt > MAX_AGE_MS) return undefined
    return { data: entry.data, savedAt: entry.savedAt }
  } catch {
    return undefined
  }
}

export function writeDashboardCache<T>(tab: string, userId: string | undefined, data: T): void {
  if (!userId) return
  try {
    const entry: Entry<T> = { v: VERSION, userId, savedAt: Date.now(), data }
    storage()?.setItem(PREFIX + tab, JSON.stringify(entry))
  } catch {
    // Full or blocked storage just means no instant view next time.
  }
}

export function clearDashboardCache(): void {
  try {
    const store = storage()
    if (!store) return
    for (const key of Object.keys(store)) {
      if (key.startsWith(PREFIX)) store.removeItem(key)
    }
  } catch {
    // Nothing stored or storage blocked -- nothing to clear.
  }
}
