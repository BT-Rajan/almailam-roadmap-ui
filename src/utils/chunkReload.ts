// Recovery from "stale build" failures after a deploy.
//
// Every page and workspace tab is a lazily loaded, content-hashed chunk
// (/assets/ProjectsPage-Bc_cXs8I.js). A deploy rebuilds the frontend and
// the old chunk files are gone, but a tab opened before the deploy still
// asks for them. The import 404s, the navigation silently fails, and the
// person is left looking at a blank or frozen page until they refresh by
// hand. Loading the page fresh picks up the new index.html and its new
// chunk names, which is exactly what the person would have done anyway.

const RELOAD_MARKER_KEY = 'serviceos:chunkReloadAt'
// If a reload already happened this recently and the chunk is *still*
// missing, the problem isn't a stale tab (the server itself is broken) and
// reloading again would just loop.
const RELOAD_LOOP_GUARD_MS = 10_000

const CHUNK_ERROR_PATTERNS = [
  /Failed to fetch dynamically imported module/i, // Chromium
  /error loading dynamically imported module/i, // Firefox
  /Importing a module script failed/i, // Safari
  /Unable to preload CSS/i, // Vite's own CSS preload
]

export function isChunkLoadError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : typeof error === 'string' ? error : ''
  return CHUNK_ERROR_PATTERNS.some((pattern) => pattern.test(message))
}

/**
 * Reloads the app at `targetPath` (or the current URL) unless it already did
 * so moments ago. Returns whether a reload was started.
 */
export function reloadForNewBuild(targetPath?: string, now: number = Date.now()): boolean {
  try {
    const last = Number(sessionStorage.getItem(RELOAD_MARKER_KEY))
    if (Number.isFinite(last) && now - last < RELOAD_LOOP_GUARD_MS) return false
    sessionStorage.setItem(RELOAD_MARKER_KEY, String(now))
  } catch {
    // Without storage there's no loop guard; don't risk a reload loop.
    return false
  }
  if (targetPath) {
    window.location.assign(targetPath)
  } else {
    window.location.reload()
  }
  return true
}
