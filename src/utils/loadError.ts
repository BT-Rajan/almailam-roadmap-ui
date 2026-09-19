import { ApiError } from '@/services/httpClient'

/**
 * Message for a store's `error` field after a failed load: keeps the
 * store's friendly sentence and appends what actually went wrong, so
 * "Unable to load contracts. Please try again." no longer looks identical
 * whether the cause was a rate limit (429), a permission problem (403),
 * a server fault (500) or a dropped connection -- the very different
 * things that message used to hide behind a bare `catch {}`.
 *
 *   HTTP 429 -> "<fallback> (HTTP 429 – Too many requests. Please slow down.)"
 *   HTTP 500 -> "<fallback> (HTTP 500 – A database error occurred. Please try again.)"
 *   no reply -> "<fallback> (Unable to reach the server. Please check ...)"
 *
 * Only API errors carry text written for users (the backend's own error
 * messages, or httpClient's network/timeout wording). Anything else is a
 * bug in our own code -- keep the friendly sentence, but log it so it
 * isn't silently swallowed.
 */
export function describeLoadError(fallback: string, error: unknown): string {
  if (!(error instanceof ApiError)) {
    console.error(`${fallback} (unexpected error, not an API error)`, error)
    return fallback
  }

  // status 0 = the request never got a response (offline/timeout); httpClient's
  // message already says so in full.
  if (error.status === 0) return `${fallback} (${error.message})`

  // extractErrorMessage falls back to "Request failed (500)" when the body
  // had no message -- don't repeat the status we're already printing.
  const hasRealMessage = error.message && !/^Request failed \(\d+\)$/.test(error.message)
  return `${fallback} (HTTP ${error.status}${hasRealMessage ? ` – ${error.message}` : ''})`
}
